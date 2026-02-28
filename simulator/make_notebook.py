import nbformat as nbf
import os

nb = nbf.v4.new_notebook()

# -----------------
# 1) CODE AND FUNCTIONS
# -----------------
logic_header = '# 1. Engine Implementation\n*(Core Monte Carlo logic and combat rules. Run this once, then scroll down to configure and run encounters.)*'
nb['cells'].append(nbf.v4.new_markdown_cell(logic_header))

logic = '''import random
import re
import copy
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def calculate_max_health(actor):
    t = actor.get('type', 'M').upper()
    d = actor.get('durability', 0)
    if t == 'A': return d * 4
    elif t == 'B': return d * 3 + 10
    elif t == 'L': return d * 2 + 10
    return d

def resolve_initiative(init_string):
    match = re.match(r'(\\d+)\\((\\d+)\\)', str(init_string))
    if match: return (int(match.group(1)) * 2) + int(match.group(2))
    return 0

def calculate_wound_dice_penalty(actor, current_hp, max_hp):
    t = actor.get('type', 'M').upper()
    hp_pct = current_hp / max_hp if max_hp > 0 else 0
    if t == 'A':
        if hp_pct < 0.25: return 2
        if hp_pct < 0.50: return 1
    elif t == 'B':
        if hp_pct < 0.333: return 2
        if hp_pct < 0.666: return 1
    elif t in ('L', 'M'):
        if hp_pct < 0.50: return 1
    return 0

def roll_attack_successes(base_dice, target_num, penalty, environment_mod):
    final_dice = max(0, base_dice - penalty + environment_mod)
    successes = 0
    if final_dice <= 0: # 0 Dice Roll Mechanics
        worst_roll = max(random.randint(1, 20), random.randint(1, 20))
        if worst_roll == target_num: successes += 2
        elif worst_roll < target_num: successes += 1
    else:
        for _ in range(final_dice):
            roll = random.randint(1, 20)
            if roll == target_num: successes += 2
            elif roll < target_num: successes += 1
    return successes

def pick_target(targets):
    living = [t for t in targets if t['current_hp'] > 0]
    if not living: return None
    weights = [sum(t.get('target_factor', [0])) for t in living]
    if sum(weights) == 0: return random.choice(living) # 0 Instance Target Factor Fix
    return random.choices(living, weights=weights, k=1)[0]

def parse_damage(damage_stat):
    match = re.match(r'(\\d+)(?:\\((\\d+)\\))?', str(damage_stat))
    return (int(match.group(1)), int(match.group(2)) if match.group(2) else 1) if match else (0, 1)

def apply_damage(target, raw_damage):
    target['current_hp'] = max(0, target['current_hp'] - max(0, raw_damage - target.get('mitigation', 0)))

def sim_combat(party_data, monster_data, max_rounds, p_env, m_env):
    p_roster = copy.deepcopy(party_data)
    m_roster = copy.deepcopy(monster_data)
    
    for p in p_roster:
        p['max_hp'] = calculate_max_health(p)
        p['current_hp'] = p['max_hp']
        p['init_score'] = resolve_initiative(p['initiative'])
        p['is_pc'] = True
        
    for m in m_roster:
        m['max_hp'] = calculate_max_health(m)
        m['current_hp'] = m['max_hp']
        m['init_score'] = resolve_initiative(m['initiative'])
        m['is_pc'] = False

    all_combatants = p_roster + m_roster
    random.shuffle(all_combatants) # Resolves identical initiative scores arbitrarily
    all_combatants.sort(key=lambda x: (x['init_score'], x['is_pc']), reverse=True) # PCs win Ties
    
    rounds_fought = 0
    while rounds_fought < max_rounds:
        rounds_fought += 1
        p_mod = p_env[min(rounds_fought-1, len(p_env)-1)]
        m_mod = m_env[min(rounds_fought-1, len(m_env)-1)]
        
        for actor in all_combatants:
            if actor['current_hp'] <= 0: continue
            
            target_pool = m_roster if actor['is_pc'] else p_roster
            env_mod = p_mod if actor['is_pc'] else m_mod
            
            targets = [t for t in target_pool if t['current_hp'] > 0]
            if not targets: continue
            
            penalty = calculate_wound_dice_penalty(actor, actor['current_hp'], actor['max_hp'])
            successes = roll_attack_successes(actor['dice'], actor['target'], penalty, env_mod)
            
            if successes > 0:
                base_dmg, max_t = parse_damage(actor['damage'])
                for _ in range(max_t):
                    target = pick_target(targets)
                    if target: apply_damage(target, base_dmg * successes)
                    
        p_alive = any(p['current_hp'] > 0 for p in p_roster)
        m_alive = any(m['current_hp'] > 0 for m in m_roster)
        
        if not p_alive: return {"outcome": "Monsters Win", "rounds": rounds_fought, "party": p_roster}
        if not m_alive: return {"outcome": "Party Wins", "rounds": rounds_fought, "party": p_roster}
            
    return {"outcome": "Time Out", "rounds": rounds_fought, "party": p_roster}

def run_monte_carlo(sim_count=1000):
    """
    Runs the combat loop N times and returns arrays of the outcomes for plotting.
    """
    results = []
    party_final_states = []
    
    for _ in range(sim_count):
        res = sim_combat(party, monsters, MaxRounds, player_enviroment_factor, monster_enviroment_factor)
        results.append(res['outcome'])
        
        if res['outcome'] == "Party Wins":
            # Track HP for survivors specifically in victorious combats
            party_final_states.append(res['party'])
            
    return results, party_final_states
'''
nb['cells'].append(nbf.v4.new_code_cell(logic))

# -----------------
# 2) PARAMETERS
# -----------------
intro = '''# 2. Combat Simulator: Encounter Configuration
Define all the global parameters and participating combatants in this cell. After saving, run the cell below to visualize the outcomes!'''
nb['cells'].append(nbf.v4.new_markdown_cell(intro))

params = '''# Global Encounter Parameters
MaxRounds = 10
simulations_to_run = 5000

# Environment Variables (Dice Adjustments per round)
player_enviroment_factor = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
monster_enviroment_factor = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# Combatant Profiles
party = [
    {
        "name": "Fighter",
        "type": "A",
        "dice": 3,
        "target": 12,
        "damage": 4,
        "durability": 10,
        "mitigation": 1,
        "initiative": "3(10)",
        "target_factor": [1, 1, 1, 1]
    },
    {
        "name": "Rogue",
        "type": "A",
        "dice": 4,
        "target": 10,
        "damage": 3,
        "durability": 8,
        "mitigation": 0,
        "initiative": "4(12)",
        "target_factor": [1, 1, 1, 1]
    },
    {
        "name": "Mage",
        "type": "A",
        "dice": 2,
        "target": 15,
        "damage": "5(2)",
        "durability": 6,
        "mitigation": 0,
        "initiative": "2(10)",
        "target_factor": [1, 1, 1, 1]
    }
]

monsters = [
    {
        "name": "Goblin Boss",
        "type": "B",
        "dice": 4,
        "target": 14,
        "damage": 5,
        "durability": 15,
        "mitigation": 2,
        "initiative": "4(12)",
        "target_factor": [1, 1, 1]
    },
    {
        "name": "Goblin Lieutenant",
        "type": "L",
        "dice": 3,
        "target": 12,
        "damage": 4,
        "durability": 10,
        "mitigation": 1,
        "initiative": "3(10)",
        "target_factor": [3, 3, 3]
    },
    {
        "name": "Goblin Minion 1",
        "type": "M",
        "dice": 2,
        "target": 10,
        "damage": 3,
        "durability": 5,
        "mitigation": 0,
        "initiative": "2(8)",
        "target_factor": [2, 2, 2]
    },
    {
        "name": "Goblin Minion 2",
        "type": "M",
        "dice": 2,
        "target": 10,
        "damage": 3,
        "durability": 5,
        "mitigation": 0,
        "initiative": "2(8)",
        "target_factor": [2, 2, 2]
    }
]'''
nb['cells'].append(nbf.v4.new_code_cell(params))

# -----------------
# 3) OUTCOMES
# -----------------
nb['cells'].append(nbf.v4.new_markdown_cell('## 3. Visualizations & Analytics\n*(Executing the simulation and plotting the aggregated data)*'))

plots = '''# Run the simulations using the parameters defined above
outcomes, victorious_parties = run_monte_carlo(sim_count=simulations_to_run)
print(f"Ran {simulations_to_run} simulations.")

# Plot the results
df_outcomes = pd.DataFrame(outcomes, columns=["Outcome"])
win_rates = df_outcomes['Outcome'].value_counts(normalize=True) * 100

print("\\n--- OVERALL WIN DISTRIBUTION ---")
print(win_rates)

plt.figure(figsize=(8, 5))
sns.barplot(x=win_rates.index, y=win_rates.values)
plt.title('Simulation Outcomes (%)')
plt.ylabel('Percentage')
plt.show()

# Extra Analytics hook: We also retrieved 'victorious_parties' 
# containing the exact remaining HP arrays of all PCs when the party wins.'''
nb['cells'].append(nbf.v4.new_code_cell(plots))

with open('CombatSimulator_MonteCarlo.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print('Notebook Generated Successfully!')
