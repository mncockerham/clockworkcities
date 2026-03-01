# Design philosophy 


I think functionally instead of object based so we should code this as a fucntional program.

Objects are fine for data structures and even some actions if you think it improves the readability and functionality.

This is a working program to help me define rules for a game I am making and we should be able to easily adjust each action and rule.

For instance I want things like attacks to be independent of other actions, we pass in the parameters and it returns the damage.

Applying damage should just be told X actor (term for player or monster) the amount of damage and any characteristics of that actor that can affect the damage done.

The final version of the notebook separates the python engine and configuration into a clean 2-cell layout. Cell 1 contains all reusable combat functions and graphing logic, while Cell 2 exposes simple parameters (Party lists, Monster lists, MaxRounds) ending with a single execution function that visualizes the results.



## Terminology
To ensure clarity across both the simulation rules and the underlying code, the following terms are used:
*   **Actor:** Any person, creature, or entity that can roll dice or take actions in combat. The base functional unit of the simulation.
*   **Player / PC (Player Character):** A specific type of Actor (always Type A - Adapted) that is controlled by a human playing the game.
*   **Party Member:** Any Actor fighting on the same side as the Players. This encompasses both PCs and any allied NPCs or summoned entities.
*   **Monster (or Enemy):** The opposing force fighting against the Party. The "Monster" side can logically be composed of any type of Actor (A, B, L, M, C), even humanoid mercenaries or rival adventurers.

# Combat Simulator: Party vs Monsters Rules

This document outlines the mechanics and logic under the hood of the Party vs Monsters Combat Simulator. The simulator runs thousands of Monte Carlo simulations to determine the win probabilities and distribution of outcomes.

## 1. Encounter Configuration

Each combatant (Player Character or Monster) is defined by a profile outlining their stats.

### Profiling a Combatant
Each combatant requires the following attributes:
*   **Name:** The identifier for the combatant.
*   **Type (`t`):** Classifies the tier and degradation rules of the combatant. These apply to both players and allies/enemies:
    *   **A - Adapted:** Peak of ability. In-universe, they are not affected by environmental degradation (this is the game/lore reason for their stats, distinct from the mechanical `enviroment_factor` impact). Used for PCs and major NPC final bosses.
    *   **B - Boss:** The next level down. The toughest leader in a major encounter.
    *   **L - Lieutenant:** Tougher adversary in a fight, but not up to a Boss level.
    *   **M - Minion:** Basically here to die bad guys.
    *   **C - Creature:** Animals, forces of nature, etc. Do not degrade. Durability is assigned as appropriate for desired strength.
*   **Dice (`d`):** The number of d20s rolled when attacking (ranges from 0 to 10).
*   ***0 Dice Mechanics:*** If a combatant has 0 dice (either statted as such or reduced via wound/environmental degradation), they roll 2 d20s and take the *highest* (worst) value. In this roll-under system, this effectively functions as "Disadvantage." That single worst result is then compared to the Target number to determine 0, 1, or 2 successes.
*   **Target (`tgt`):** The Maximum number required to score a "success" on a d20 (ranges from 1 to 20) rolls higher than the target number generate 0 success.
*                       ** Rolling target number will count as 2 success 
*   **Damage (`dam`):** The base damage dealt *per success*, and optionally the maximum number of targets hit.
    *   *Format 1:* Standard single target (e.g., `4` or `"4"`).
    *   *Format 2:* Multi-target / AoE (e.g., `"5(3)"` indicates 5 damage per success, hitting up to 3 distinct targets). *Note:* For now, treat multi-attacks as normal 1-success attacks per target, randomly assigning targets using standard rules.
*   **Durability (`dur`):** Number represents base toughness
*   **Mitigation (`mit`):** [Optional, Default 0] Flat damage reduction applied against each incoming hit. Damage cannot be reduced below 0. Mitigation applies to *each* hit of a multi-target/AoE attack individually.
*   **Initiative (`ini`):** is stored as  X(t) X is dice rolled t is target number calcuation is + 2 for every success plust target number
    ** Example 1: 4(10) 4 dice 10 target number  4 * 2 + 10 = 18
    ** Example 2: 4(12) 4 dice 12 target number  4 * 2 + 12 = 20
    ** This controlls turn order.  It is only rolled once at the end of combat turn counts down from Highnumber to lowest number, players always win ties against monsters. Ties between monsters, or ties between players, are resolved arbitrarily (e.g., order in the array).
*   **Target Factor (`tf`):** An array determining the probability of an Actor being chosen as the target of an attack. The index of the array directly corresponds to the **number of living allies** on that team (`original_size - current_living`). Example: If a Rogue has `[2, 4, 5]` and the party starts with 3, they use 2 while everyone is alive, 4 when one ally drops, and 5 when they are the last one standing.
*   **Focus Factor (`ff`):** A percentage value (e.g. 80) representing the chance this combatant will focus fire on a primary target instead of randomly attacking.
*   **Priority (`pri`):** A string or numerical indicator mapping combatants for priority targeting purposes. Lower values indicate higher priority.
    
### Global Encounter Parameters
The simulation requires the following configurable levers to be defined, ideally in a single configuration cell:
*   **MaxRounds (`MaxRounds`):** The maximum number of combat rounds allowed before the simulation yields a "Time out" failure (e.g., 10).
*   **Player Environment Factor (`player_enviroment_factor`):** An array listing dice adjustments for the party per round. The last value applies to all subsequent rounds once exhausted. (Default: 0).
*   **Monster Environment Factor (`monster_enviroment_factor`):** An array listing dice adjustments for the monsters per round. The last value applies to all subsequent rounds once exhausted. (Default: 0).

### Defining Combatants
The configuration should include distinct sections to define the specific combatants participating:
*   **Players:** A list or dictionary defining 1 to X Player Characters.
*   **Monsters:** A list or dictionary defining 1 to X Creatures/Enemies.

** Calculated Values
* **Health.   This varies on each creature Type and has an impact on dice rolled Health roll adjustments can never reduce dice below 0 dice
*   *** A  total health durability * 4   When health is less than 25% of total rol 2 less dice When health is less than 50% of total rol 1 less dice
*   *** B  total health durability * 3 + 10 when health is less than 1/3 roll 2 less dice when health is less than 2/3 roll 1 less dice
*   *** L  total health durability * 2 + 10 when health is less than 1/2 roll 1 less dice
*   *** M  total health durability  health is less than 50% roll 1 less dice
*   *** C  total health durability Always roll max dice

** Targeting Matrix 
**  Extract the `target_factor` weighting index for each living target based on their remaining team size.
**  Add all current weights together to get the total target factor pool.
**  Divide each combatant's weight by the pool to get their probability of being attacked.
**  *0 Instance Rule:* If the total weight of all living valid targets evaluates to 0, all attacks are assigned randomly across them with equal probability.



---

## 3. Turn Resolution Logic


For every living attacker:

### Step A: Generating Raw Damage
1.  **Success Calculation:** The simulator determines the number of successes rolled based on the combatant's `dice` and `target` stats.
    *   *Note on Dice Odds:* A typical roll matching the `target` yields 2 successes. A roll under that target number is 1 success. Rolls over the target number yield 0 successes.
2.  **Base Damage Multiplication:** 
    `Raw Damage = Total Successes * Base Damage`
  
---

## 4. End of Turn & Outcome Tracking

Repeat the combat rounds with any adjustments needed for enviroment, damage, number of actors on each side 

Outcomes will have 3 results
* Party Wins all monsters are dead
* Monsters Win all party members are dead
* Time out  If the combat goes on for more than `MaxRounds` this is a failure condition as not good for a table RPG

At the end of the simulation, the tool generates summary visualization graphs:
*   The overall Win Distribution % (Party vs Monsters vs Timeout).
*   The death risk percentage for each individual party member (calculated only from victorious encounters).
*   A boxplot scale showing the distribution of remaining HP of party members that survived the fight.
*   A Stacked Bar Chart mapping the probability of the combat ending exactly on each Round, visually separated by color for the three Outcome conditions.
