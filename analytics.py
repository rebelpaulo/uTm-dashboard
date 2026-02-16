#!/usr/bin/env python3
"""
Dashboard Analytics - Revenge House Party
Analisa ficheiros Excel de vendas e gera relatórios
"""

import pandas as pd
import json
from datetime import datetime
from collections import defaultdict
import sys

def analyze_sales(filepath):
    """Analisa o ficheiro Excel de vendas"""
    
    # Ler o Excel
    df = pd.read_excel(filepath)
    
    # Limpar nomes de colunas (remover BOM se existir)
    df.columns = [col.replace('ï»¿', '') for col in df.columns]
    
    # Converter data
    df['Payment date (UTC)'] = pd.to_datetime(df['Payment date (UTC)'])
    df['Date'] = df['Payment date (UTC)'].dt.date
    
    # Análise geral
    total_sales = df['Paid'].sum()
    total_tickets = df['Tickets'].sum()
    total_orders = len(df)
    avg_ticket = total_sales / total_tickets if total_tickets > 0 else 0
    
    # Análise por dia
    daily = df.groupby('Date').agg({
        'Paid': 'sum',
        'Tickets': 'sum',
        'Order #': 'count'
    }).reset_index()
    daily.columns = ['Date', 'Revenue', 'Tickets', 'Orders']
    
    # Análise por UTM
    utm_analysis = df.groupby(['utm_source', 'utm_medium', 'utm_content']).agg({
        'Paid': 'sum',
        'Tickets': 'sum',
        'Order #': 'count'
    }).reset_index()
    utm_analysis.columns = ['Source', 'Medium', 'Content', 'Revenue', 'Tickets', 'Orders']
    utm_analysis = utm_analysis.sort_values('Revenue', ascending=False)
    
    # Análise por campanha (utm_campaign)
    campaign_analysis = df.groupby('utm_campaign').agg({
        'Paid': 'sum',
        'Tickets': 'sum',
        'Order #': 'count'
    }).reset_index()
    campaign_analysis.columns = ['Campaign', 'Revenue', 'Tickets', 'Orders']
    campaign_analysis = campaign_analysis.sort_values('Revenue', ascending=False)
    
    return {
        'summary': {
            'total_sales': float(total_sales),
            'total_tickets': int(total_tickets),
            'total_orders': int(total_orders),
            'avg_ticket': float(avg_ticket)
        },
        'daily': daily.to_dict('records'),
        'utm': utm_analysis.to_dict('records'),
        'campaigns': campaign_analysis.to_dict('records'),
        'raw_data': df.to_dict('records')
    }

def compare_files(old_file, new_file):
    """Compara dois ficheiros e mostra diferenças"""
    
    old_data = analyze_sales(old_file)
    new_data = analyze_sales(new_file)
    
    # Calcular diferenças
    sales_diff = new_data['summary']['total_sales'] - old_data['summary']['total_sales']
    tickets_diff = new_data['summary']['total_tickets'] - old_data['summary']['total_tickets']
    orders_diff = new_data['summary']['total_orders'] - old_data['summary']['total_orders']
    
    # Encontrar novas vendas
    old_orders = set(pd.read_excel(old_file)['Order #'].tolist())
    new_df = pd.read_excel(new_file)
    new_orders = set(new_df['Order #'].tolist())
    
    new_sales_orders = new_orders - old_orders
    
    comparison = {
        'sales_diff': float(sales_diff),
        'tickets_diff': int(tickets_diff),
        'orders_diff': int(orders_diff),
        'new_orders': list(new_sales_orders),
        'old_summary': old_data['summary'],
        'new_summary': new_data['summary']
    }
    
    return comparison, new_data

def generate_report(data, comparison=None):
    """Gera relatório em formato legível"""
    
    report = []
    report.append("=" * 60)
    report.append("📊 DASHBOARD VENDAS - REVENGE HOUSE PARTY")
    report.append("=" * 60)
    report.append("")
    
    # Resumo geral
    s = data['summary']
    report.append("💰 RESUMO GERAL")
    report.append("-" * 40)
    report.append(f"Total Vendas: €{s['total_sales']:,.2f}")
    report.append(f"Total Bilhetes: {s['total_tickets']:,}")
    report.append(f"Total Transações: {s['total_orders']:,}")
    report.append(f"Ticket Médio: €{s['avg_ticket']:.2f}")
    report.append("")
    
    # Comparação se existir
    if comparison:
        report.append("📈 COMPARAÇÃO COM FICHEIRO ANTERIOR")
        report.append("-" * 40)
        report.append(f"Novas vendas: €{comparison['sales_diff']:,.2f} ({comparison['orders_diff']} transações)")
        report.append(f"Novos bilhetes: {comparison['tickets_diff']:,}")
        report.append(f"Novos Order IDs: {len(comparison['new_orders'])}")
        report.append("")
    
    # Top UTM Sources
    report.append("🎯 TOP FONTES (UTM)")
    report.append("-" * 40)
    for i, utm in enumerate(data['utm'][:5], 1):
        source = utm['Source'] or 'Direct'
        medium = utm['Medium'] or 'none'
        content = utm['Content'] or '-'
        report.append(f"{i}. {source} / {medium} / {content}")
        report.append(f"   €{utm['Revenue']:,.2f} | {utm['Tickets']} bilhetes | {utm['Orders']} vendas")
        report.append("")
    
    # Vendas por dia
    report.append("📅 VENDAS POR DIA")
    report.append("-" * 40)
    for day in data['daily'][-7:]:  # Últimos 7 dias
        report.append(f"{day['Date']}: €{day['Revenue']:,.2f} ({day['Tickets']} bilhetes)")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)

def update_dashboard_html(data, output_path='index.html'):
    """Atualiza o dashboard HTML com dados reais"""
    
    # Preparar dados para JavaScript
    daily_dates = [str(d['Date']) for d in data['daily']]
    daily_revenue = [float(d['Revenue']) for d in data['daily']]
    daily_tickets = [int(d['Tickets']) for d in data['daily']]
    
    utm_labels = [f"{u['Source'] or 'Direct'}" for u in data['utm'][:5]]
    utm_values = [float(u['Revenue']) for u in data['utm'][:5]]
    
    summary = data['summary']
    
    # Criar novo HTML com dados reais
    html_content = f'''<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Vendas - Revenge House Party</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }}
        h1 {{ font-size: 2.5rem; margin-bottom: 10px; background: linear-gradient(90deg, #e94560, #ff6b6b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ color: #888; font-size: 1.1rem; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card h3 {{
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #888;
            margin-bottom: 12px;
        }}
        .card .value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #e94560;
        }}
        .chart-container {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .chart-container h3 {{
            margin-bottom: 20px;
            font-size: 1.2rem;
        }}
        .two-columns {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{
            color: #888;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 1px;
        }}
        tr:hover {{ background: rgba(255,255,255,0.03); }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-ig {{ background: #e4405f; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎉 Revenge House Party</h1>
            <p class="subtitle">Dashboard de Vendas & Analytics</p>
            <p style="color: #666; margin-top: 10px;">Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </header>

        <div class="grid">
            <div class="card">
                <h3>Total de Vendas</h3>
                <div class="value">€{summary['total_sales']:,.0f}</div>
            </div>
            <div class="card">
                <h3>Bilhetes Vendidos</h3>
                <div class="value">{summary['total_tickets']:,}</div>
            </div>
            <div class="card">
                <h3>Ticket Médio</h3>
                <div class="value">€{summary['avg_ticket']:.0f}</div>
            </div>
            <div class="card">
                <h3>Transações</h3>
                <div class="value">{summary['total_orders']:,}</div>
            </div>
        </div>

        <div class="two-columns">
            <div class="chart-container">
                <h3>📊 Vendas por Dia</h3>
                <canvas id="dailyChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>🎯 Vendas por Fonte (UTM)</h3>
                <canvas id="utmChart"></canvas>
            </div>
        </div>

        <div class="chart-container">
            <h3>📈 Performance por Fonte</h3>
            <table>
                <thead>
                    <tr>
                        <th>Fonte</th>
                        <th>Medium</th>
                        <th>Content</th>
                        <th>Vendas</th>
                        <th>Total (€)</th>
                        <th>Bilhetes</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f"<tr><td><span class='badge badge-ig'>{u['Source'] or 'Direct'}</span></td><td>{u['Medium'] or '-'}</td><td>{u['Content'] or '-'}</td><td>{u['Orders']}</td><td>€{u['Revenue']:,.0f}</td><td>{u['Tickets']}</td></tr>" for u in data['utm'][:10]])}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Dados reais do Excel
        const salesData = {{
            dates: {json.dumps(daily_dates)},
            amounts: {json.dumps(daily_revenue)},
            tickets: {json.dumps(daily_tickets)}
        }};

        const utmData = {{
            labels: {json.dumps(utm_labels)},
            values: {json.dumps(utm_values)},
            colors: ['#e4405f', '#f77737', '#1877f2', '#4ade80', '#888']
        }};

        new Chart(document.getElementById('dailyChart'), {{
            type: 'line',
            data: {{
                labels: salesData.dates,
                datasets: [{{
                    label: 'Vendas (€)',
                    data: salesData.amounts,
                    borderColor: '#e94560',
                    backgroundColor: 'rgba(233, 69, 96, 0.1)',
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ labels: {{ color: '#fff' }} }} }},
                scales: {{
                    x: {{ ticks: {{ color: '#888' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    y: {{ ticks: {{ color: '#888' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }}
                }}
            }}
        }});

        new Chart(document.getElementById('utmChart'), {{
            type: 'doughnut',
            data: {{
                labels: utmData.labels,
                datasets: [{{
                    data: utmData.values,
                    backgroundColor: utmData.colors,
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ color: '#fff', padding: 20 }} }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 analytics.py <ficheiro_excel> [ficheiro_anterior]")
        sys.exit(1)
    
    new_file = sys.argv[1]
    old_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if old_file:
        comparison, data = compare_files(old_file, new_file)
        print(generate_report(data, comparison))
    else:
        data = analyze_sales(new_file)
        print(generate_report(data))
        
        # Atualizar dashboard HTML
        update_dashboard_html(data)
        print("\n✅ Dashboard HTML atualizado: index.html")
