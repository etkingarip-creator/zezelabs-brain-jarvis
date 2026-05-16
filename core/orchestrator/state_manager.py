# ZOM v6.2 State Manager - LangGraph-inspired Persistence Layer
# Jarvis'in görevler arasındaki durumunu (state) ve geçmişini yöneten hafıza merkezi.

import json
import time

class ZomStateManager:
    """
    Jarvis'in Stateful (Durumsal) Hafızası. 
    Her görevi bir 'Graf Düğümü' olarak görür ve ilerlemeyi kaydeder.
    """
    def __init__(self):
        self.checkpoints = {} # Görev ID -> State verisi

    def save_checkpoint(self, task_id, node_name, current_state):
        """Görev sürecinde bir durak (checkpoint) oluşturur."""
        checkpoint = {
            "node": node_name,
            "timestamp": time.time(),
            "state": current_state,
            "version": len(self.checkpoints.get(task_id, {}).get("history", [])) + 1
        }
        
        if task_id not in self.checkpoints:
            self.checkpoints[task_id] = {"history": []}
            
        self.checkpoints[task_id]["history"].append(checkpoint)
        self.checkpoints[task_id]["current"] = checkpoint
        print(f"[StateManager] 💾 Checkpoint Kaydedildi: {task_id} @ {node_name}")

    def load_checkpoint(self, task_id):
        """Görevi en son başarılı duraktan geri yükler (Time Travel)."""
        return self.checkpoints.get(task_id, {}).get("current")

    def rollback(self, task_id, steps=1):
        """Görevi belirli bir adım geriye çeker."""
        history = self.checkpoints.get(task_id, {}).get("history", [])
        if len(history) > steps:
            self.checkpoints[task_id]["history"] = history[:-steps]
            self.checkpoints[task_id]["current"] = self.checkpoints[task_id]["history"][-1]
            return True
        return False

state_manager = ZomStateManager()
