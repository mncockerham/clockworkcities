import json

file_path = r"c:\Users\mncoc\OneDrive\Documents\AI Assist\Professional\clockworkcities\Dice_Odds.ipynb"

with open(file_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_func_source = [
    "import numpy as np\n",
    "\n",
    "def calculate_matrix_comparison(num_dice_array, target_array):\n",
    "    if isinstance(num_dice_array, int): num_dice_array = [num_dice_array]\n",
    "    if isinstance(target_array, int): target_array = [target_array]\n",
    "    \n",
    "    num_dice_array = sorted(list(set(num_dice_array)))\n",
    "    target_array = sorted([t for t in target_array if 2 <= t <= 20])\n",
    "    \n",
    "    if not target_array or not num_dice_array:\n",
    "        print(\"Valid arrays for both targets and dice must be provided.\")\n",
    "        return\n",
    "        \n",
    "    col_width = 14\n",
    "    \n",
    "    # Header\n",
    "    header = f\"{'Dice':<8} | \"\n",
    "    for target in target_array:\n",
    "        h_col = f\"TAR {target}\"\n",
    "        header += f\"{h_col:>{col_width}} | \"\n",
    "        \n",
    "    sep = \"-\" * len(header)\n",
    "    eq_sep = \"=\" * len(header)\n",
    "    \n",
    "    exact_distributions = {}\n",
    "    cumul_distributions = {}\n",
    "    \n",
    "    for num_dice in num_dice_array:\n",
    "        exact_distributions[num_dice] = {}\n",
    "        cumul_distributions[num_dice] = {}\n",
    "        for target in target_array:\n",
    "            p_0 = (20 - target) / 20.0\n",
    "            p_1 = (target - 1) / 20.0\n",
    "            p_2 = 1.0 / 20.0\n",
    "            \n",
    "            single_die_poly = np.array([p_0, p_1, p_2])\n",
    "            dist_poly = np.polynomial.polynomial.polypow(single_die_poly, num_dice)\n",
    "            percentages = dist_poly * 100\n",
    "            \n",
    "            exact_vals = []\n",
    "            cumul_vals = []\n",
    "            \n",
    "            for s in range(10):\n",
    "                chance_exact = percentages[s] if s < len(percentages) else 0.0\n",
    "                chance_cumul = np.sum(percentages[s:]) if s < len(percentages) else 0.0\n",
    "                \n",
    "                exact_vals.append((str(s), chance_exact))\n",
    "                if s == 0:\n",
    "                    cumul_vals.append((str(s), chance_exact))\n",
    "                else:\n",
    "                    cumul_vals.append((str(s), chance_cumul))\n",
    "                    \n",
    "            chance_10plus = np.sum(percentages[10:]) if 10 < len(percentages) else 0.0\n",
    "            exact_vals.append((\"10+\", chance_10plus))\n",
    "            cumul_vals.append((\"10+\", chance_10plus))\n",
    "            \n",
    "            exact_distributions[num_dice][target] = exact_vals\n",
    "            cumul_distributions[num_dice][target] = cumul_vals\n",
    "            \n",
    "    def print_matrix(title, dist_dict, is_cumulative):\n",
    "        print(title)\n",
    "        print(eq_sep)\n",
    "        print(header)\n",
    "        print(sep)\n",
    "        \n",
    "        for num_dice in num_dice_array:\n",
    "            for line_idx in range(11):\n",
    "                if line_idx == 0:\n",
    "                    row_str = f\"{num_dice:<8} | \"\n",
    "                else:\n",
    "                    row_str = f\"{' ':<8} | \"\n",
    "                    \n",
    "                for target in target_array:\n",
    "                    label, chance = dist_dict[num_dice][target][line_idx]\n",
    "                    \n",
    "                    if is_cumulative and line_idx == 0:\n",
    "                        val_str = f\"[{chance:05.2f}]\"\n",
    "                    else:\n",
    "                        if chance == 0:\n",
    "                            val_str = \"0.00%\"\n",
    "                        elif chance < 0.005 and chance > 0:\n",
    "                            val_str = \"<0.01%\"\n",
    "                        else:\n",
    "                            val_str = f\"{chance:.2f}%\"\n",
    "                            \n",
    "                    visible_len = len(label) + 2 + len(val_str)\n",
    "                    pad = \" \" * max(0, col_width - visible_len)\n",
    "                    bold_label = f\"\\033[1m{label}\\033[0m\"\n",
    "                    \n",
    "                    row_str += f\"{pad}{bold_label}: {val_str} | \"\n",
    "                print(row_str)\n",
    "            print(sep)\n",
    "        print(eq_sep)\n",
    "        print(\"\\n\")\n",
    "        \n",
    "    print_matrix(\"Full Distribution Matrix (EXACT %, 0 to 10+ successes)\", exact_distributions, False)\n",
    "    print_matrix(\"Full Distribution Matrix (X OR MORE %, 0 to 10+ successes)\", cumul_distributions, True)\n"
]

new_md_source = [
    "***\n",
    "## 2D Matrix: Dice Pools vs Target Numbers\n",
    "This function creates cross-comparison matrices. It outputs the exact percentage chance and cumulative percentage chance of rolling 0 to 10+ successes for every combination of dice pool and target number."
]

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        if any('def calculate_matrix_comparison' in line for line in cell['source']):
            cell['source'] = new_func_source
            cell['outputs'] = []
            cell['execution_count'] = None
    elif cell['cell_type'] == 'markdown':
        if any('2D Matrix: Dice Pools vs Target Numbers' in line for line in cell['source']):
            cell['source'] = new_md_source

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=4)
