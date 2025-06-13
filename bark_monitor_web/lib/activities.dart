import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

class Activities extends StatefulWidget {
  const Activities({super.key, required this.serverUrl});

  @override
  State<Activities> createState() => _ActivitiesState();
  final String serverUrl;
}

class _ActivitiesState extends State<Activities> {
  Map<DateTime, String> activities = {};

  @override
  void initState() {
    fetchActivities();
    super.initState();
  }

  // Function to fetch posts using Dio
  Future<void> fetchActivities() async {
    try {
      var response = await Dio().get('${widget.serverUrl}activities');
      setState(() {
        String activitiesStr = response.data["activities"];
        activities = {};
        for (var line in activitiesStr.split("\n")) {
          DateTime date = DateTime.parse(line.split("---")[0]);
          activities[date] = line.split("---")[1];
        }
      });
    } catch (e) {
      print('Error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text("Activities:", style: TextStyle(fontSize: 20)),
            IconButton(
              onPressed: fetchActivities,
              icon: Icon(Icons.replay_outlined),
            ),
          ],
        ),

        Expanded(
          child: Container(
            constraints: BoxConstraints(maxWidth: 600),
            child: ListView.builder(
              padding: const EdgeInsets.all(50),
              itemCount: activities.length,
              itemBuilder: (context, index) {
                final entry = activities.entries.elementAt(index);
                return Card(
                  child: ListTile(
                    title: Text(entry.key.toString()),
                    subtitle: Text(entry.value),
                  ),
                );
              },
            ),
          ),
        ),
      ],
    );
  }
}
