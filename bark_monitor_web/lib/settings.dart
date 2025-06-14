import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

class Settings extends StatefulWidget {
  const Settings({super.key, required this.serverUrl});

  @override
  State<Settings> createState() => _SettingsState();
  final String serverUrl;
}

class _SettingsState extends State<Settings> {
  @override
  void initState() {
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          'Settings',
          style: TextStyle(fontSize: 35, fontWeight: FontWeight.bold),
        ),
        Text("Server: ${widget.serverUrl}"),
      ],
    );
  }
}
