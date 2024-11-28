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


# --- File Upload and Processing Routes ---
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


# --- Manual Input Route ---
@app.route('/manual', methods=['POST'])
def manual_input():
    data = request.form.get('data')
    interval = request.form.get('interval')  # Interval is optional

    if not data:
        return jsonify({'error': 'Error: No data provided. Please input a valid comma-separated list of numbers.'})

    try:
        # Validate input: ensure it contains only numbers and single commas
        parts = data.split(',')
        numbers = [float(part.strip()) for part in parts if part.strip()]
        if not numbers:
            raise ValueError("No valid numbers found.")

        # Ungrouped Calculations
        ungrouped_results = calculate_ungrouped(numbers)

        if interval:  # If interval is provided, perform grouped calculations
            interval = float(interval)
            if interval <= 0:
                raise ValueError("Interval must be a positive number.")

            grouped_results = calculate_grouped(numbers, interval)
            return jsonify({
                'ungrouped': ungrouped_results,
                'grouped': grouped_results
            })
        else:
            return jsonify({'ungrouped': ungrouped_results})

    except ValueError:
        return jsonify({'error': 'Error: Invalid input. Please input numbers only and separate them with a single comma.'})
    except Exception as e:
        return jsonify({'error': f'Error processing manual data: {str(e)}'})


# --- Calculation and Histogram Functions ---

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


def calculate_ungrouped(numbers):
    mean = sum(numbers) / len(numbers)
    median = sorted(numbers)[len(numbers) // 2] if len(numbers) % 2 != 0 else \
        sum(sorted(numbers)[len(numbers) // 2 - 1:len(numbers) // 2 + 1]) / 2
    mode = pd.Series(numbers).mode().tolist()

    # Generate Histogram
    plt.hist(numbers, bins=5, color='blue', alpha=0.7)
    plt.title('Ungrouped Data Histogram')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return {
        'mean': mean,
        'median': median,
        'mode': mode,
        'plot_url': f'data:image/png;base64,{plot_url}'
    }


def calculate_grouped(numbers, interval):
    # Calculate ranges
    min_value, max_value = min(numbers), max(numbers)
    bins = []
    frequencies = []

    lower_bound = min_value
    while lower_bound < max_value:
        upper_bound = lower_bound + interval
        bins.append(f"{int(lower_bound)} - {int(upper_bound) - 1}")
        frequencies.append(sum(lower_bound <= x < upper_bound for x in numbers))
        lower_bound = upper_bound

    # Midpoints
    midpoints = [(float(bin.split(' - ')[0]) + float(bin.split(' - ')[1])) / 2 for bin in bins]

    # Grouped Mean
    total_frequency = sum(frequencies)
    mean = sum(mid * freq for mid, freq in zip(midpoints, frequencies)) / total_frequency

    # Grouped Median
    cumulative_frequencies = [sum(frequencies[:i + 1]) for i in range(len(frequencies))]
    median_class_index = next(i for i, cf in enumerate(cumulative_frequencies) if cf >= total_frequency / 2)
    median_lower_bound = float(bins[median_class_index].split(' - ')[0])
    cumulative_frequency_before_median = cumulative_frequencies[median_class_index - 1] if median_class_index > 0 else 0
    median_frequency = frequencies[median_class_index]
    median = median_lower_bound + ((total_frequency / 2 - cumulative_frequency_before_median) / median_frequency) * interval

    # Grouped Mode
    max_frequency = max(frequencies)
    mode_class_index = frequencies.index(max_frequency)
    mode_lower_bound = float(bins[mode_class_index].split(' - ')[0])
    f1 = frequencies[mode_class_index]
    f0 = frequencies[mode_class_index - 1] if mode_class_index > 0 else 0
    f2 = frequencies[mode_class_index + 1] if mode_class_index < len(frequencies) - 1 else 0
    mode = mode_lower_bound + ((f1 - f0) / ((f1 - f0) + (f1 - f2))) * interval if f1 != 0 else None

    # Generate Grouped Histogram
    plt.hist(numbers, bins=[float(bin.split(' - ')[0]) for bin in bins] + [float(bins[-1].split(' - ')[1])], color='green', alpha=0.7)
    plt.title('Grouped Data Histogram')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return {
        'frequency_table': {
            'bins': bins,
            'frequencies': frequencies,
        },
        'mean': mean,
        'median': median,
        'mode': mode,
        'plot_url': f'data:image/png;base64,{plot_url}'
    }


if __name__ == '__main__':
    app.run(debug=True)
