import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend for Matplotlib

import os
import io
import base64
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or request.files['file'].filename == '':
        return jsonify({'error': 'No file uploaded. Please upload a valid CSV file.'})
    
    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        df = pd.read_csv(file_path)
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()  # Filter numeric columns
        return jsonify({'file_path': file_path, 'numeric_columns': numeric_columns})
    except Exception as e:
        return jsonify({'error': f'Error reading CSV file: {str(e)}'})

@app.route('/measure-of-tendency')
def measure_of_tendency():
    return render_template('measure-of-tendency.html')

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/probability')
def probability():
    return render_template('probability.html')

@app.route('/process', methods=['POST'])
def process_data():
    column = request.form.get('column')
    file_path = request.form.get('file_path')

    if not column or not file_path:
        return jsonify({'error': 'Column or file path missing. Please upload the CSV and select a column.'})

    try:
        df = pd.read_csv(file_path)
        if column not in df.columns:
            return jsonify({'error': f'Column "{column}" not found in the CSV file.'})
        
        # Extract and clean data from the selected column
        numbers = df[column].dropna().tolist()
        numbers = list(map(float, numbers))

        return calculate_and_generate_histogram(numbers, column)

    except Exception as e:
        return jsonify({'error': f'Error processing column "{column}": {str(e)}'})

@app.route('/manual', methods=['POST'])
def manual_input():
    data = request.form.get('data')

    if not data:
        return jsonify({'error': 'Error: No data provided. Please input a valid comma-separated list of numbers.'})

    try:
        # Validate input: ensure it contains only numbers and single commas
        parts = data.split(',')
        numbers = [float(part.strip()) for part in parts if part.strip()]
        
        # If no valid numbers were parsed, raise an error
        if not numbers:
            raise ValueError("No valid numbers found.")
        
        return calculate_and_generate_histogram(numbers, "Manual Input")
    except ValueError:
        return jsonify({'error': 'Error: Invalid input. Please input numbers only and separate them with a single comma.'})
    except Exception as e:
        return jsonify({'error': f'Error processing manual data: {str(e)}'})


def calculate_and_generate_histogram(numbers, title):
    # Calculate Central Tendencies
    mean = sum(numbers) / len(numbers)
    median = sorted(numbers)[len(numbers) // 2] if len(numbers) % 2 != 0 else \
        sum(sorted(numbers)[len(numbers) // 2 - 1:len(numbers) // 2 + 1]) / 2
    mode = pd.Series(numbers).mode().tolist()

    # Generate Histogram
    plt.hist(numbers, bins=5, color='blue', alpha=0.7)
    plt.title(f'Histogram of {title}')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.tight_layout()

    # Save plot to a string buffer
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return jsonify({
        'mean': mean,
        'median': median,
        'mode': mode,
        'plot_url': f'data:image/png;base64,{plot_url}'
    })

if __name__ == '__main__':
    app.run(debug=True)
