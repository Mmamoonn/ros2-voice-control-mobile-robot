#!/usr/bin/env python3
"""
generate_graphs.py
------------------
Reads evaluation_results/latency_log.csv and generates publication-quality
graphs for the final project report.

Run after performance_evaluator completes:
  python3 ~/ros2_ws/src/voice_robot/voice_robot/generate_graphs.py
"""

import os
import csv
import statistics
import matplotlib
matplotlib.use('Agg')   # headless — no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

INPUT_DIR  = os.path.expanduser('~/ros2_ws/evaluation_results')
OUTPUT_DIR = os.path.expanduser('~/ros2_ws/evaluation_results/graphs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

COMMANDS        = ['forward', 'backward', 'left', 'right', 'stop']
COMMAND_COLOURS = {
    'forward':  '#2196F3',
    'backward': '#FF5722',
    'left':     '#4CAF50',
    'right':    '#FF9800',
    'stop':     '#9C27B0',
}


# ── Load data ─────────────────────────────────────────────────
def load_latency(path):
    records = []
    with open(path) as f:
        for row in csv.DictReader(f):
            records.append({
                'command':    row['command'],
                'latency_ms': float(row['latency_ms']),
                'accurate':   row['accurate'] == 'True',
            })
    return records


# ── Graph 1: Latency per command (bar chart with error bars) ──
def plot_latency_bar(records):
    fig, ax = plt.subplots(figsize=(9, 5))

    x_positions = np.arange(len(COMMANDS))
    means, stds, colours = [], [], []

    for cmd in COMMANDS:
        lats = [r['latency_ms'] for r in records if r['command'] == cmd]
        means.append(statistics.mean(lats) if lats else 0)
        stds.append(statistics.stdev(lats) if len(lats) > 1 else 0)
        colours.append(COMMAND_COLOURS[cmd])

    bars = ax.bar(x_positions, means, yerr=stds, capsize=6,
                  color=colours, alpha=0.85, edgecolor='white',
                  linewidth=0.8, error_kw={'elinewidth': 1.5, 'ecolor': '#333'})

    # 500 ms target line from proposal
    ax.axhline(y=500, color='red', linestyle='--',
               linewidth=1.5, label='Target: 500 ms')

    # Value labels on bars
    for bar, mean, std in zip(bars, means, stds):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + std + 8,
                f'{mean:.1f}', ha='center', va='bottom',
                fontsize=9, fontweight='bold')

    ax.set_xticks(x_positions)
    ax.set_xticklabels([c.capitalize() for c in COMMANDS], fontsize=11)
    ax.set_ylabel('Latency (ms)', fontsize=12)
    ax.set_title('Command Execution Latency by Type\n'
                 '(Mean ± Std Dev)', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.set_ylim(0, max(means) * 1.4 + 60)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, 'latency_by_command.png')
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out}')


# ── Graph 2: Latency over time (line chart) ───────────────────
def plot_latency_timeline(records):
    fig, ax = plt.subplots(figsize=(11, 4))

    x = range(1, len(records) + 1)
    y = [r['latency_ms'] for r in records]
    colours = [COMMAND_COLOURS[r['command']] for r in records]

    ax.plot(x, y, color='#607D8B', linewidth=1.2,
            alpha=0.6, zorder=1, label='Latency')
    ax.scatter(x, y, c=colours, s=60, zorder=2, edgecolors='white',
               linewidths=0.5)

    ax.axhline(y=statistics.mean(y), color='#2196F3',
               linestyle='--', linewidth=1.5,
               label=f'Mean: {statistics.mean(y):.1f} ms')
    ax.axhline(y=500, color='red', linestyle='--',
               linewidth=1.5, label='Target: 500 ms')

    # Legend patches for commands
    patches = [mpatches.Patch(color=COMMAND_COLOURS[c],
                               label=c.capitalize())
               for c in COMMANDS]
    ax.legend(handles=patches + [
        plt.Line2D([0], [0], color='#2196F3',
                   linestyle='--', label=f'Mean: {statistics.mean(y):.1f} ms'),
        plt.Line2D([0], [0], color='red',
                   linestyle='--', label='Target: 500 ms'),
    ], fontsize=8, loc='upper right', ncol=2)

    ax.set_xlabel('Command Sequence Number', fontsize=11)
    ax.set_ylabel('Latency (ms)', fontsize=11)
    ax.set_title('End-to-End Latency Over Command Sequence',
                 fontsize=13, fontweight='bold')
    ax.set_xlim(0.5, len(records) + 0.5)
    ax.set_ylim(0, max(y) * 1.3 + 40)
    ax.grid(alpha=0.25, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, 'latency_timeline.png')
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out}')


# ── Graph 3: Command accuracy (stacked bar) ───────────────────
def plot_accuracy(records):
    fig, ax = plt.subplots(figsize=(9, 5))

    x_positions = np.arange(len(COMMANDS))
    correct_counts   = []
    incorrect_counts = []

    for cmd in COMMANDS:
        cmd_records = [r for r in records if r['command'] == cmd]
        correct   = sum(1 for r in cmd_records if r['accurate'])
        incorrect = len(cmd_records) - correct
        correct_counts.append(correct)
        incorrect_counts.append(incorrect)

    bars1 = ax.bar(x_positions, correct_counts,
                   color='#4CAF50', alpha=0.85,
                   label='Correct', edgecolor='white')
    bars2 = ax.bar(x_positions, incorrect_counts,
                   bottom=correct_counts,
                   color='#F44336', alpha=0.85,
                   label='Incorrect', edgecolor='white')

    # Percentage labels
    for i, (c, inc) in enumerate(zip(correct_counts, incorrect_counts)):
        total = c + inc
        if total > 0:
            pct = (c / total) * 100
            ax.text(i, total + 0.1, f'{pct:.0f}%',
                    ha='center', va='bottom',
                    fontsize=10, fontweight='bold')

    # 90% target line from proposal
    total_per_cmd = max(correct_counts[i] + incorrect_counts[i]
                        for i in range(len(COMMANDS)))
    ax.axhline(y=total_per_cmd * 0.9, color='orange',
               linestyle='--', linewidth=1.5,
               label='Target: 90% accuracy')

    ax.set_xticks(x_positions)
    ax.set_xticklabels([c.capitalize() for c in COMMANDS], fontsize=11)
    ax.set_ylabel('Number of Commands', fontsize=12)
    ax.set_title('Command Execution Accuracy by Type',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, 'command_accuracy.png')
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out}')


# ── Graph 4: Latency distribution (histogram) ─────────────────
def plot_latency_histogram(records):
    fig, ax = plt.subplots(figsize=(8, 4))

    latencies = [r['latency_ms'] for r in records]
    ax.hist(latencies, bins=15, color='#2196F3',
            alpha=0.75, edgecolor='white', linewidth=0.8)

    mean_lat   = statistics.mean(latencies)
    median_lat = statistics.median(latencies)

    ax.axvline(mean_lat,   color='#FF5722', linestyle='--',
               linewidth=2, label=f'Mean: {mean_lat:.1f} ms')
    ax.axvline(median_lat, color='#4CAF50', linestyle='--',
               linewidth=2, label=f'Median: {median_lat:.1f} ms')
    ax.axvline(500, color='red', linestyle=':',
               linewidth=1.5, label='Target: 500 ms')

    ax.set_xlabel('Latency (ms)', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('Latency Distribution — All Commands',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, 'latency_histogram.png')
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out}')


# ── Main ──────────────────────────────────────────────────────
if __name__ == '__main__':
    latency_path = os.path.join(INPUT_DIR, 'latency_log.csv')

    if not os.path.exists(latency_path):
        print(f'ERROR: {latency_path} not found.')
        print('Run performance_evaluator first:')
        print('  ros2 run voice_robot performance_evaluator')
        exit(1)

    print('Loading results...')
    records = load_latency(latency_path)
    print(f'Loaded {len(records)} records.')

    print('Generating graphs...')
    plot_latency_bar(records)
    plot_latency_timeline(records)
    plot_accuracy(records)
    plot_latency_histogram(records)

    print(f'\nAll graphs saved to: {OUTPUT_DIR}/')
    print('Graphs:')
    print('  latency_by_command.png   — bar chart per command type')
    print('  latency_timeline.png     — latency over sequence')
    print('  command_accuracy.png     — correct vs incorrect stacked bar')
    print('  latency_histogram.png    — distribution of all latencies')
