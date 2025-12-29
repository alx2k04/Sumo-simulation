import traci
import os, sys
import time # Needed to control the visualization speed

# --- Configuration Section ---

SUMOCFG = "cross.sumocfg"
TLS_ID = "C" 
THRESHOLD = 5 # Queue length (in number of vehicles) to trigger a phase switch
MIN_GREEN = 10 # Minimum time (in seconds) for a green light before a switch is allowed
YELLOW_DURATION = 3 

# Visualization speed control (0.1 means 10 simulation steps per real second)
SLEEP_TIME = 0.1 

# Phase indexes defined in simple_tl.add.xml
PHASE_H_GREEN = 0
PHASE_H_YELLOW = 1
PHASE_V_GREEN = 2
PHASE_V_YELLOW = 3

# Lanes to monitor for queue length (assumes E0_0 and E2_0 are the relevant lanes)
LANE_H = "E0_0" 
LANE_V = "E2_0" 

# --- Environment Setup (Crucial for TraCI) ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare the environment variable 'SUMO_HOME' so the Python script can find TraCI.")
# -----------------------------------------------


def run():
    """Main simulation loop for adaptive traffic light control."""
    step = 0
    current_phase = PHASE_H_GREEN
    phase_timer = 0
    
    # traci.start launches the SUMO-GUI application
    traci.start(["sumo-gui", "-c", SUMOCFG, "--start"])
    
    print("TraCI connected. Starting adaptive control.")
    
    # Loop runs until 1000 steps are complete, matching cross.sumocfg
    while step < 1000: 
        traci.simulationStep()
        
        # Slow down visualization
        if SLEEP_TIME > 0:
            time.sleep(SLEEP_TIME)
        
        phase_timer += 1
        
        # Read queue length using waiting time as a proxy
        queue_H = traci.lane.getWaitingTime(LANE_H) 
        queue_V = traci.lane.getWaitingTime(LANE_V) 

        # --- PHASE SWITCHING LOGIC ---
        
        # 1. Check for Yellow Phase completion
        if current_phase == PHASE_H_YELLOW and phase_timer >= YELLOW_DURATION:
            traci.trafficlight.setPhase(TLS_ID, PHASE_V_GREEN)
            current_phase = PHASE_V_GREEN
            phase_timer = 0
            
        elif current_phase == PHASE_V_YELLOW and phase_timer >= YELLOW_DURATION:
            traci.trafficlight.setPhase(TLS_ID, PHASE_H_GREEN)
            current_phase = PHASE_H_GREEN
            phase_timer = 0
            
        # 2. Check for Green Phase switching condition (adaptive)
        # Horizontal Green (H-Green) -> Switch to H-Yellow?
        elif current_phase == PHASE_H_GREEN:
            # Condition: Min green time reached AND high queue on opposing road (V)
            if phase_timer >= MIN_GREEN and queue_V > THRESHOLD:
                traci.trafficlight.setPhase(TLS_ID, PHASE_H_YELLOW)
                current_phase = PHASE_H_YELLOW
                phase_timer = 0
            # Condition: Max duration reached (30s)
            elif phase_timer >= 30: 
                 traci.trafficlight.setPhase(TLS_ID, PHASE_H_YELLOW)
                 current_phase = PHASE_H_YELLOW
                 phase_timer = 0
        
        # Vertical Green (V-Green) -> Switch to V-Yellow?
        elif current_phase == PHASE_V_GREEN:
            # Condition: Min green time reached AND high queue on opposing road (H)
            if phase_timer >= MIN_GREEN and queue_H > THRESHOLD:
                traci.trafficlight.setPhase(TLS_ID, PHASE_V_YELLOW)
                current_phase = PHASE_V_YELLOW
                phase_timer = 0
            # Condition: Max duration reached (30s)
            elif phase_timer >= 30: 
                 traci.trafficlight.setPhase(TLS_ID, PHASE_V_YELLOW)
                 current_phase = PHASE_V_YELLOW
                 phase_timer = 0

        step += 1

    traci.close()
    sys.stdout.flush()

if __name__ == "__main__":
    run()