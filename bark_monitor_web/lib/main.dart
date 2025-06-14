import 'package:bark_monitor_web/activities.dart';
import 'package:bark_monitor_web/settings.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Bark Monitor',
      darkTheme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          brightness: Brightness.dark,
          seedColor: const Color.fromARGB(255, 255, 238, 82),
        ),
      ),
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.yellow),
      ),
      home: const MyHomePage(title: 'Bark Monitor'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  // This widget is the home page of your application. It is stateful, meaning
  // that it has a State object (defined below) that contains fields that affect
  // how it looks.

  // This class is the configuration for the state. It holds the values (in this
  // case the title) provided by the parent (in this case the App widget) and
  // used by the build method of the State. Fields in a Widget subclass are
  // always marked "final".

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  bool recording = false;
  String serverUrl = "http://127.0.0.1:8000/";
  late final List<Widget> _widgetOptions;

  @override
  void initState() {
    super.initState();
    fetchStatus(); // Fetch posts when the app starts
    _widgetOptions = <Widget>[
      Activities(serverUrl: serverUrl),
      Settings(serverUrl: serverUrl),
    ];
  }

  int _selectedIndex = 0;

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  // Function to fetch posts using Dio
  Future<void> start() async {
    try {
      await Dio().post('${serverUrl}start');
      setState(() {
        fetchStatus();
      });
    } catch (e) {
      print('Error: $e');
    }
  }

  // Function to fetch posts using Dio
  Future<void> stop() async {
    try {
      await Dio().post('${serverUrl}stop');
      setState(() {
        fetchStatus();
      });
    } catch (e) {
      print('Error: $e');
    }
  }

  // Function to fetch posts using Dio
  Future<void> fetchStatus() async {
    try {
      var response = await Dio().get('${serverUrl}status');
      setState(() {
        recording = response.data["result"];
      });
    } catch (e) {
      print('Error: $e');
    }
  }

  // Function to fetch posts using Dio
  Future<void> fetchLastAudio() async {
    try {
      var response = await Dio().get('${serverUrl}last_audio');
      setState(() {
        recording = response.data["result"];
      });
    } catch (e) {
      print('Error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    // This method is rerun every time setState is called, for instance as done
    // by the _incrementCounter method above.
    //
    // The Flutter framework has been optimized to make rerunning build methods
    // fast, so that you can just rebuild anything that needs updating rather
    // than having to individually change instances of widgets.
    return Scaffold(
      // appBar: AppBar(
      //   // TRY THIS: Try changing the color here to a specific color (to
      //   // Colors.amber, perhaps?) and trigger a hot reload to see the AppBar
      //   // change color while the other colors stay the same.
      //   backgroundColor: recording
      //       ? Colors.green
      //       : Theme.of(context).colorScheme.inversePrimary,
      //   // Here we take the value from the MyHomePage object that was created by
      //   // the App.build method, and use it to set our appbar title.
      //   title: Text(widget.title),
      // ),
      body: Center(child: _widgetOptions.elementAt(_selectedIndex)),
      bottomNavigationBar: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          LinearProgressIndicator(
            value: recording ? null : 0,
            color: Colors.green,
          ),
          BottomNavigationBar(
            items: const <BottomNavigationBarItem>[
              BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
              BottomNavigationBarItem(
                icon: Icon(Icons.settings),
                label: 'Settings',
              ),
            ],
            currentIndex: _selectedIndex,
            selectedItemColor: Theme.of(context).colorScheme.primary,
            onTap: _onItemTapped,
          ),
        ],
      ),

      floatingActionButton: FloatingActionButton.large(
        onPressed: recording ? stop : start,
        backgroundColor: recording
            ? Colors.green
            : Theme.of(context).colorScheme.inversePrimary,
        child: recording
            ? const Icon(Icons.stop)
            : const Icon(Icons.play_arrow),
      ),
    );
  }
}
