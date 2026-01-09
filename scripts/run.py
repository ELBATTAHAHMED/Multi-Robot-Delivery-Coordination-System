"""
Multi-Robot Delivery Coordination System - Simulation Runner
Runs experiments comparing coordination mechanisms with multiple scenarios
"""

from model import WarehouseModel
import matplotlib.pyplot as plt
import pandas as pd
import os


def run_single_simulation(
    num_robots=5,
    coordination_mechanism="cnp",
    order_mode="fixed_orders",
    order_count=10,
    order_rate=0.3,
    max_steps=200,
    grid_size=20,
    robot_failure_step=None,
    clustered_orders=False,
    cluster_center=None,
    cluster_radius=5,
    verbose=True
):
    """Run a single simulation and return results"""
    if verbose:
        print(f"\n{'='*60}")
        print(f"Running simulation: {coordination_mechanism.upper()}")
        print(f"Robots: {num_robots}, Mode: {order_mode}", end="")
        if order_mode == "fixed_orders":
            print(f", Orders: {order_count}", end="")
        else:
            print(f", Order Rate: {order_rate}", end="")
        print(f", Steps: {max_steps}, Grid: {grid_size}x{grid_size}")
        if robot_failure_step:
            print(f"Robot Failure: Step {robot_failure_step}")
        if clustered_orders:
            print(f"Clustered Orders: Center {cluster_center}, Radius {cluster_radius}")
        print(f"{'='*60}")
    
    model = WarehouseModel(
        num_robots=num_robots,
        grid_width=grid_size,
        grid_height=grid_size,
        coordination_mechanism=coordination_mechanism,
        order_generation_mode=order_mode,
        order_generation_rate=order_rate,
        fixed_order_count=order_count,
        max_steps=max_steps,
        robot_failure_step=robot_failure_step,
        clustered_orders=clustered_orders,
        cluster_center=cluster_center,
        cluster_radius=cluster_radius
    )
    
    step = 0
    while model.running and step < max_steps:
        model.step()
        step += 1
        if verbose and step % 50 == 0:
            print(f"  Step {step}/{max_steps} - Completed: {len(model.completed_orders)}/{model.orders_generated_count}")
    
    metrics = model.get_metrics()
    
    model_data = model.datacollector.get_model_vars_dataframe()
    agent_data = model.datacollector.get_agent_vars_dataframe()
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"RESULTS - {coordination_mechanism.upper()}")
        print(f"{'='*60}")
        print(f"Total Orders Generated: {metrics['total_orders_generated']}")
        print(f"Total Orders Completed: {metrics['total_orders_completed']}")
        print(f"Throughput (orders/step): {metrics['throughput']:.4f}")
        print(f"Efficiency (orders/distance): {metrics['efficiency']:.4f}")
        print(f"Total Distance Traveled: {metrics['total_distance']:.2f}")
        print(f"Avg Distance per Robot: {metrics['avg_distance_per_robot']:.2f}")
        print(f"Avg Tasks per Robot: {metrics['avg_tasks_per_robot']:.2f}")
        print(f"Task Fairness (variance): {metrics['task_fairness_variance']:.2f}")
        print(f"Total Idle Time: {metrics['total_idle_time']}")
        print(f"Attempted Conflicts: {metrics['attempted_conflicts']}")
        print(f"Hard Blocks: {metrics['hard_blocks']}")
        print(f"Total Conflicts: {metrics['total_conflicts']}")
        print(f"Avg Completion Delay: {metrics['avg_completion_delay']:.2f} steps")
        print(f"Avg Battery Level End: {metrics['avg_battery_end']:.2f}")
        print(f"{'='*60}\n")
    
    return {
        'metrics': metrics,
        'model_data': model_data,
        'agent_data': agent_data,
        'model': model
    }


def export_to_csv(model_data, agent_data, scenario_name, mechanism):
    """Export model and agent data to CSV files"""
    safe_scenario = scenario_name.lower().replace(" ", "_")
    
    model_filename = f"model_{safe_scenario}_{mechanism}.csv"
    model_data.to_csv(model_filename, index=True)
    print(f"   💾 Exported: {model_filename}")
    
    agent_filename = f"agent_{safe_scenario}_{mechanism}.csv"
    agent_data.to_csv(agent_filename, index=True)
    print(f"   💾 Exported: {agent_filename}")


def create_comparison_visualizations(cnp_results, greedy_results, centralized_results=None, scenario_name="Default"):
    """Create comparison visualizations for 2 or 3 mechanisms"""
    
    num_mechanisms = 3 if centralized_results else 2
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f'Multi-Robot Delivery Coordination - {scenario_name}', fontsize=16, fontweight='bold')
    
    cnp_data = cnp_results['model_data']
    greedy_data = greedy_results['model_data']
    centralized_data = centralized_results['model_data'] if centralized_results else None
    
    colors = {'cnp': '#2563eb', 'greedy': '#dc2626', 'centralized': '#16a34a'}
    
    # 1. Throughput
    ax = axes[0, 0]
    ax.plot(cnp_data.index, cnp_data['Throughput'], label='CNP', linewidth=2, color=colors['cnp'])
    ax.plot(greedy_data.index, greedy_data['Throughput'], label='Greedy', linewidth=2, color=colors['greedy'])
    if centralized_data is not None:
        ax.plot(centralized_data.index, centralized_data['Throughput'], label='Centralized', linewidth=2, color=colors['centralized'])
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Orders Completed')
    ax.set_title('Throughput Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. Total distance
    ax = axes[0, 1]
    ax.plot(cnp_data.index, cnp_data['Total_Distance'], label='CNP', linewidth=2, color=colors['cnp'])
    ax.plot(greedy_data.index, greedy_data['Total_Distance'], label='Greedy', linewidth=2, color=colors['greedy'])
    if centralized_data is not None:
        ax.plot(centralized_data.index, centralized_data['Total_Distance'], label='Centralized', linewidth=2, color=colors['centralized'])
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Total Distance Traveled')
    ax.set_title('Distance Traveled Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Average battery
    ax = axes[0, 2]
    ax.plot(cnp_data.index, cnp_data['Avg_Battery'], label='CNP', linewidth=2, color=colors['cnp'])
    ax.plot(greedy_data.index, greedy_data['Avg_Battery'], label='Greedy', linewidth=2, color=colors['greedy'])
    if centralized_data is not None:
        ax.plot(centralized_data.index, centralized_data['Avg_Battery'], label='Centralized', linewidth=2, color=colors['centralized'])
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Average Battery Level')
    ax.set_title('Battery Usage')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Active orders
    ax = axes[1, 0]
    ax.plot(cnp_data.index, cnp_data['Active_Orders'], label='CNP', linewidth=2, color=colors['cnp'])
    ax.plot(greedy_data.index, greedy_data['Active_Orders'], label='Greedy', linewidth=2, color=colors['greedy'])
    if centralized_data is not None:
        ax.plot(centralized_data.index, centralized_data['Active_Orders'], label='Centralized', linewidth=2, color=colors['centralized'])
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Active Orders')
    ax.set_title('Active Orders Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. Conflicts over time
    ax = axes[1, 1]
    ax.plot(cnp_data.index, cnp_data['Total_Conflicts'], label='CNP', linewidth=2, color=colors['cnp'])
    ax.plot(greedy_data.index, greedy_data['Total_Conflicts'], label='Greedy', linewidth=2, color=colors['greedy'])
    if centralized_data is not None:
        ax.plot(centralized_data.index, centralized_data['Total_Conflicts'], label='Centralized', linewidth=2, color=colors['centralized'])
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Total Conflicts')
    ax.set_title('Conflicts Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 6. Performance metrics comparison
    ax = axes[1, 2]
    metrics_labels = ['Throughput\n(x100)', 'Efficiency\n(x10)', 'Fairness\n(variance)']
    cnp_values = [
        cnp_results['metrics']['throughput'] * 100,
        cnp_results['metrics']['efficiency'] * 10,
        cnp_results['metrics']['task_fairness_variance'],
    ]
    
    greedy_values = [
        greedy_results['metrics']['throughput'] * 100,
        greedy_results['metrics']['efficiency'] * 10,
        greedy_results['metrics']['task_fairness_variance'],
    ]
    
    x = range(len(metrics_labels))
    width = 0.25 if centralized_results else 0.35
    offset = 1.0 if centralized_results else 1.5
    
    ax.bar([i - width for i in x], cnp_values, width, label='CNP', color=colors['cnp'])
    ax.bar([i for i in x], greedy_values, width, label='Greedy', color=colors['greedy'])
    
    if centralized_results:
        centralized_values = [
            centralized_results['metrics']['throughput'] * 100,
            centralized_results['metrics']['efficiency'] * 10,
            centralized_results['metrics']['task_fairness_variance'],
        ]
        ax.bar([i + width for i in x], centralized_values, width, label='Centralized', color=colors['centralized'])
    
    ax.set_ylabel('Value (normalized)')
    ax.set_title('Performance Metrics')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_labels)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_file = os.path.join(os.getcwd(), f'warehouse_{scenario_name.lower().replace(" ", "_")}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"   📊 Visualization saved to: {output_file}")
    plt.close()


def run_scenario_analysis():
    """Run multiple scenarios as required by the PDF"""
    
    print("\n" + "="*60)
    print("SCENARIO ANALYSIS - PDF REQUIREMENTS")
    print("="*60)
    
    scenarios = [
        {
            "name": "Light Load",
            "robots": 5,
            "order_mode": "fixed_orders",
            "order_count": 10,
            "order_rate": 0.3,
            "steps": 200,
            "grid_size": 20,
            "failure_step": None,
            "clustered": False,
            "cluster_center": None,
            "cluster_radius": 5
        },
        {
            "name": "Medium Load",
            "robots": 5,
            "order_mode": "fixed_orders",
            "order_count": 30,
            "order_rate": 0.3,
            "steps": 200,
            "grid_size": 20,
            "failure_step": None,
            "clustered": False,
            "cluster_center": None,
            "cluster_radius": 5
        },
        {
            "name": "Heavy Load",
            "robots": 5,
            "order_mode": "fixed_orders",
            "order_count": 50,
            "order_rate": 0.3,
            "steps": 200,
            "grid_size": 20,
            "failure_step": None,
            "clustered": False,
            "cluster_center": None,
            "cluster_radius": 5
        },
        {
            "name": "Robot Failure",
            "robots": 5,
            "order_mode": "fixed_orders",
            "order_count": 30,
            "order_rate": 0.3,
            "steps": 200,
            "grid_size": 20,
            "failure_step": 80,
            "clustered": False,
            "cluster_center": None,
            "cluster_radius": 5
        },
        {
            "name": "Clustered Orders",
            "robots": 5,
            "order_mode": "fixed_orders",
            "order_count": 30,
            "order_rate": 0.3,
            "steps": 200,
            "grid_size": 20,
            "failure_step": None,
            "clustered": True,
            "cluster_center": (10, 10),
            "cluster_radius": 5
        },
        {
            "name": "Dynamic Orders",
            "robots": 5,
            "order_mode": "probabilistic",
            "order_count": 30,
            "order_rate": 0.4,
            "steps": 200,
            "grid_size": 20,
            "failure_step": None,
            "clustered": False,
            "cluster_center": None,
            "cluster_radius": 5
        },
        {
            "name": "Congestion Test",
            "robots": 12,
            "order_mode": "fixed_orders",
            "order_count": 40,
            "order_rate": 0.3,
            "steps": 200,
            "grid_size": 12,
            "failure_step": None,
            "clustered": False,
            "cluster_center": None,
            "cluster_radius": 5
        }
    ]

    all_results = []
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"Scenario: {scenario['name']}")
        print(f"{'='*60}")
        
        cnp_result = run_single_simulation(
            num_robots=scenario['robots'],
            coordination_mechanism="cnp",
            order_mode=scenario['order_mode'],
            order_count=scenario['order_count'],
            order_rate=scenario['order_rate'],
            max_steps=scenario['steps'],
            grid_size=scenario['grid_size'],
            robot_failure_step=scenario['failure_step'],
            clustered_orders=scenario['clustered'],
            cluster_center=scenario['cluster_center'],
            cluster_radius=scenario['cluster_radius'],
            verbose=True
        )
        
        print(f"\n   Exporting CNP data...")
        export_to_csv(cnp_result['model_data'], cnp_result['agent_data'], 
                     scenario['name'], 'cnp')
        
        greedy_result = run_single_simulation(
            num_robots=scenario['robots'],
            coordination_mechanism="greedy",
            order_mode=scenario['order_mode'],
            order_count=scenario['order_count'],
            order_rate=scenario['order_rate'],
            max_steps=scenario['steps'],
            grid_size=scenario['grid_size'],
            robot_failure_step=scenario['failure_step'],
            clustered_orders=scenario['clustered'],
            cluster_center=scenario['cluster_center'],
            cluster_radius=scenario['cluster_radius'],
            verbose=True
        )
        
        print(f"\n   Exporting Greedy data...")
        export_to_csv(greedy_result['model_data'], greedy_result['agent_data'], 
                     scenario['name'], 'greedy')
        
        centralized_result = run_single_simulation(
            num_robots=scenario['robots'],
            coordination_mechanism="centralized",
            order_mode=scenario['order_mode'],
            order_count=scenario['order_count'],
            order_rate=scenario['order_rate'],
            max_steps=scenario['steps'],
            grid_size=scenario['grid_size'],
            robot_failure_step=scenario['failure_step'],
            clustered_orders=scenario['clustered'],
            cluster_center=scenario['cluster_center'],
            cluster_radius=scenario['cluster_radius'],
            verbose=True
        )
        
        print(f"\n   Exporting Centralized data...")
        export_to_csv(centralized_result['model_data'], centralized_result['agent_data'], 
                     scenario['name'], 'centralized')
        
        create_comparison_visualizations(cnp_result, greedy_result, centralized_result, scenario['name'])
        
        all_results.append({
            'scenario': scenario['name'],
            'cnp': cnp_result['metrics'],
            'greedy': greedy_result['metrics'],
            'centralized': centralized_result['metrics']
        })
    
    summary_data = []
    for result in all_results:
        for mechanism in ['cnp', 'greedy', 'centralized']:
            m = result[mechanism]
            summary_data.append({
                'Scenario': result['scenario'],
                'Mechanism': mechanism.upper(),
                'Generated': m['total_orders_generated'],
                'Completed': m['total_orders_completed'],
                'Throughput': f"{m['throughput']:.4f}",
                'Efficiency': f"{m['efficiency']:.4f}",
                'Distance': f"{m['total_distance']:.2f}",
                'Fairness_Var': f"{m['task_fairness_variance']:.2f}",
                'Idle_Time': m['total_idle_time'],
                'Attempted_Conflicts': m['attempted_conflicts'],
                'Hard_Blocks': m['hard_blocks'],
                'Total_Conflicts': m['total_conflicts'],
                'Avg_Completion_Delay': f"{m['avg_completion_delay']:.2f}",
                'Avg_Battery_End': f"{m['avg_battery_end']:.2f}",
            })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv('summary_scenarios_mechanisms.csv', index=False)
    print(f"\n   💾 Summary table exported to: summary_scenarios_mechanisms.csv")
    
    print("\n" + "="*60)
    print("COMPREHENSIVE SCENARIO SUMMARY")
    print("="*60 + "\n")
    
    print(f"{'Scenario':<20} {'Mechanism':<12} {'Generated':<12} {'Completed':<12} {'Throughput':<12} {'Conflicts':<12}")
    print("-" * 88)
    
    for result in all_results:
        for mechanism in ['cnp', 'greedy', 'centralized']:
            m = result[mechanism]
            print(f"{result['scenario']:<20} {mechanism.upper():<12} {m['total_orders_generated']:<12} {m['total_orders_completed']:<12} {m['throughput']:<12.4f} {m['total_conflicts']:<12}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("MULTI-ROBOT DELIVERY COORDINATION SYSTEM")
    print("Complete MAS Analysis - 3 Mechanisms, 7 Scenarios")
    print("="*60)
    
    run_scenario_analysis()
    
    print("\n✅ All simulations complete!")
    print("\n📈 Generated Visualizations (7 scenarios):")
    print("   - warehouse_light_load.png")
    print("   - warehouse_medium_load.png")
    print("   - warehouse_heavy_load.png")
    print("   - warehouse_robot_failure.png")
    print("   - warehouse_clustered_orders.png")
    print("   - warehouse_dynamic_orders.png")
    print("   - warehouse_congestion_test.png")
    print("\n💾 Generated CSV Files (21 per scenario: 3 mechanisms × 2 files each + summary):")
    print("   - model_*.csv and agent_*.csv for each mechanism")
    print("   - summary_scenarios_mechanisms.csv (comprehensive table)")
