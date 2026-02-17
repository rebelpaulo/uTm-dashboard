#!/usr/bin/env python3
"""
Dashboard Analytics - Revenge House Party
Analisa ficheiros Excel de vendas e gera relatórios
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import sys

def analyze_sales(filepath):
    """Analisa o ficheiro de vendas (Excel ou CSV)"""
    
    # Detectar formato e ler o ficheiro
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath, sep=';')
    else:
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
    
    # Calcular filtros de data com breakdown UTM
    filters = calculate_date_filters(df)
    
    return {
        'summary': {
            'total_sales': float(total_sales),
            'total_tickets': int(total_tickets),
            'total_orders': int(total_orders),
            'avg_ticket': float(avg_ticket)
        },
        'filters': filters,
        'daily': daily.to_dict('records'),
        'utm': utm_analysis.to_dict('records'),
        'raw_data': df.to_dict('records')
    }

def calculate_date_filters(df):
    """Calcula métricas para diferentes períodos de tempo com breakdown UTM"""
    
    now = datetime.now()
    
    # Último dia (24h)
    last_24h = now - timedelta(hours=24)
    df_last_day = df[df['Payment date (UTC)'] >= last_24h]
    
    # Última semana (7 dias)
    last_week = now - timedelta(days=7)
    df_last_week = df[df['Payment date (UTC)'] >= last_week]
    
    # Último mês (30 dias)
    last_month = now - timedelta(days=30)
    df_last_month = df[df['Payment date (UTC)'] >= last_month]
    
    def calc_metrics(df_period):
        if len(df_period) == 0:
            return {'sales': 0, 'tickets': 0, 'orders': 0, 'avg': 0, 'utm': {}}
        
        sales = float(df_period['Paid'].sum())
        tickets = int(df_period['Tickets'].sum())
        orders = len(df_period)
        avg = float(sales / tickets) if tickets > 0 else 0
        
        # Breakdown por UTM
        utm_breakdown = {}
        utm_groups = df_period.groupby(['utm_source', 'utm_medium', 'utm_content'])
        for (source, medium, content), group in utm_groups:
            key = f"{source}_{medium}_{content}".replace(' ', '_').replace('{{', '').replace('}}', '')
            utm_breakdown[key] = {
                'name': f"{source} - {content}" if content else f"{source} - {medium}",
                'sales': float(group['Paid'].sum()),
                'tickets': int(group['Tickets'].sum()),
                'orders': len(group)
            }
        
        return {'sales': sales, 'tickets': tickets, 'orders': orders, 'avg': avg, 'utm': utm_breakdown}
    
    return {
        'all': calc_metrics(df),
        'last_day': calc_metrics(df_last_day),
        'last_week': calc_metrics(df_last_week),
        'last_month': calc_metrics(df_last_month)
    }

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
    
    # Filtros de data
    report.append("📅 VENDAS POR PERÍODO")
    report.append("-" * 40)
    for period, values in data['filters'].items():
        label = {'all': 'Todo o período', 'last_day': 'Último dia', 
                 'last_week': 'Última semana', 'last_month': 'Último mês'}[period]
        report.append(f"{label}: €{values['sales']:,.2f} ({values['tickets']} bilhetes)")
    report.append("")
    
    # Top UTM Sources
    report.append("🎯 TOP FONTES (UTM)")
    report.append("-" * 40)
    for i, utm in enumerate(data['utm'][:5], 1):
        source = utm['Source'] or 'Direct'
        content = utm['Content'] or '-'
        report.append(f"{i}. {source} - {content}")
        report.append(f"   €{utm['Revenue']:,.2f} | {utm['Tickets']} bilhetes | {utm['Orders']} vendas")
        report.append("")
    
    report.append("=" * 60)
    
    return "\n".join(report)

def export_for_html(data, output_file='data.json'):
    """Exporta dados para JSON ser usado pelo HTML"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    return output_file

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 analytics.py <ficheiro_excel>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    data = analyze_sales(filepath)
    
    print(generate_report(data))
    
    # Exportar para JSON
    export_for_html(data, 'data.json')
    print("\n✅ Dados exportados: data.json")
