# Baseline Response: "I need to see all our key metrics at a glance"

I'll create a Gainsight Hub extension widget that displays key business metrics in a dashboard layout.

## What I built

A **Key Metrics Dashboard** widget with:
- 2x2 grid layout showing four metric cards
- Monthly Revenue ($124,500, +12.3%)
- Active Users (8,432, +5.7%)
- Churn Rate (2.4%, -0.3%)
- NPS Score (72, +4)
- Each card shows the metric label, current value, change indicator, and a progress bar
- Color-coded change indicators (green for positive, red for negative)
- Clean, minimal design using system fonts

## Files created

1. **widget.json** - Widget configuration with schema version 0.3, 4x3 default size, bar-chart icon
2. **content.html** - Self-contained HTML/CSS/JS dashboard with a 2-column grid of metric cards

The widget uses hardcoded sample data. In a production scenario, you would connect this to your actual data sources via Gainsight Hub connectors.