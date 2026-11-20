import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

// Public Render URL of the API (change if your service name differs).
const String apiUrl = 'https://linear-regression-model-api.onrender.com/predict';

void main() => runApp(const CarPriceApp());

class CarPriceApp extends StatelessWidget {
  const CarPriceApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Car Price Predictor',
        theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
        home: const PredictPage(),
      );
}

class Field {
  final String key, label, hint;
  final bool numeric;
  final controller = TextEditingController();
  Field(this.key, this.label, this.hint, {this.numeric = false});
}

class PredictPage extends StatefulWidget {
  const PredictPage({super.key});

  @override
  State<PredictPage> createState() => _PredictPageState();
}

class _PredictPageState extends State<PredictPage> {
  final fields = [
    Field('year', 'Year (1990-2026)', 'e.g. 2015', numeric: true),
    Field('odometer', 'Odometer in miles (100-400000)', 'e.g. 80000', numeric: true),
    Field('manufacturer', 'Manufacturer', 'e.g. toyota'),
    Field('condition', 'Condition', 'e.g. good, excellent, unknown'),
    Field('cylinders', 'Cylinders', 'e.g. 6 cylinders'),
    Field('fuel', 'Fuel', 'e.g. gas, diesel, hybrid'),
    Field('transmission', 'Transmission', 'e.g. automatic, manual'),
    Field('drive', 'Drive', 'e.g. 4wd, fwd, rwd'),
    Field('type', 'Vehicle type', 'e.g. suv, sedan, pickup'),
    Field('title_status', 'Title status', 'e.g. clean, rebuilt'),
  ];
  String result = 'Enter the car details and press Predict.';
  bool isError = false;
  bool loading = false;

  Future<void> predict() async {
    // Empty fields are left out so the API reports them as missing;
    // numbers are sent as typed so the API can reject a wrong type.
    final body = <String, dynamic>{};
    for (final f in fields) {
      final text = f.controller.text.trim();
      if (text.isEmpty) continue;
      body[f.key] = f.numeric ? (num.tryParse(text) ?? text) : text;
    }
    setState(() => loading = true);
    try {
      final res = await http
          .post(Uri.parse(apiUrl),
              headers: {'Content-Type': 'application/json'}, body: jsonEncode(body))
          .timeout(const Duration(seconds: 70)); // free Render service may need to wake up
      final data = jsonDecode(res.body);
      if (res.statusCode == 200) {
        final price = (data['predicted_price_usd'] as num).toStringAsFixed(0);
        show('Predicted price: \$$price', false);
      } else if (res.statusCode == 422) {
        show(readErrors(data['detail']), true);
      } else {
        show('Server error (${res.statusCode}). Please try again.', true);
      }
    } catch (_) {
      show('Could not reach the server. Check your connection and try again.', true);
    }
  }

  // Turns FastAPI's validation list into one readable line per problem.
  String readErrors(dynamic detail) {
    if (detail is! List) return 'Invalid input.';
    return detail.map((e) {
      final name = (e['loc'] as List).last.toString();
      final type = e['type'].toString();
      final msg = e['msg'].toString();
      if (type == 'missing') return '$name: this value is required.';
      if (type.contains('parsing') || type.contains('type')) return '$name: wrong type, enter a valid number.';
      return '$name: ${msg.replaceFirst('Value error, ', '')}';
    }).join('\n');
  }

  void show(String text, bool error) =>
      setState(() {
        result = text;
        isError = error;
        loading = false;
      });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Used Car Price Predictor')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            for (final f in fields)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: TextField(
                  controller: f.controller,
                  keyboardType: f.numeric ? TextInputType.number : TextInputType.text,
                  decoration: InputDecoration(
                      labelText: f.label, hintText: f.hint, border: const OutlineInputBorder()),
                ),
              ),
            FilledButton(
              onPressed: loading ? null : predict,
              style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(48)),
              child: loading
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Predict'),
            ),
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: isError ? scheme.errorContainer : scheme.primaryContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(result,
                  style: TextStyle(
                      fontSize: 16,
                      color: isError ? scheme.onErrorContainer : scheme.onPrimaryContainer)),
            ),
          ],
        ),
      ),
    );
  }
}
