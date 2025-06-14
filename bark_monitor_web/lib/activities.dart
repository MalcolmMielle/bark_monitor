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
  int timeBarked = 0;

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
        if (activitiesStr == "") {
          return;
        }
        for (var line in activitiesStr.split("\n")) {
          DateTime date = DateTime.parse(line.split("---")[0]);
          activities[date] = line.split("---")[1];
        }
      });
    } catch (e) {
      print('Error: $e');
    }
  }

  // Function to fetch posts using Dio
  Future<void> fetchTimeBarked() async {
    try {
      var response = await Dio().get('${widget.serverUrl}activities');
      setState(() {
        timeBarked = response.data["time barked"];
      });
    } catch (e) {
      print('Error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          constraints: BoxConstraints(maxWidth: 400),
          child: Card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                ListTile(
                  leading: Icon(Icons.thumb_up_alt_sharp),
                  title: Text("Time barked today"),
                  subtitle: Text("$timeBarked seconds"),
                ),
                TextButton.icon(
                  onPressed: fetchTimeBarked,
                  label: Text("Update"),
                  icon: Icon(Icons.replay_outlined),
                ),
              ],
            ),
          ),
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Activities',
              style: TextStyle(fontSize: 35, fontWeight: FontWeight.bold),
            ),
            IconButton(
              onPressed: fetchActivities,
              icon: Icon(Icons.replay_outlined),
            ),
          ],
        ),

        activities.isEmpty
            ? Container(
                constraints: BoxConstraints(maxWidth: 400),
                child: Card(
                  child: ListTile(
                    leading: Icon(Icons.catching_pokemon),
                    title: Text("No activities today"),
                    subtitle: Text("Watson is being a good dog :)."),
                  ),
                ),
              )
            : Expanded(
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
