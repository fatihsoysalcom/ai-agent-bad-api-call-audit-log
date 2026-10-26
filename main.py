import datetime
import json

class AuditLog:
    """Manages and stores audit log entries."""
    def __init__(self):
        self.entries = []

    def log_event(self, event_type, details):
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "details": details
        }
        self.entries.append(log_entry)
        print(f"[AUDIT] {json.dumps(log_entry)}")

    def get_logs(self):
        return self.entries

class ProductService:
    """Simulates an API for managing product inventory."""
    def __init__(self, audit_log):
        self.products = {
            "Laptop": {"id": "P001", "name": "Laptop", "quantity": 100},
            "Mouse": {"id": "P002", "name": "Mouse", "quantity": 50},
            "Keyboard": {"id": "P003", "name": "Keyboard", "quantity": 75},
            "Tablet": {"id": "P004", "name": "Tablet", "quantity": 30}
        }
        self.audit_log = audit_log

    def _get_product_by_name(self, product_name):
        for prod in self.products.values():
            if prod["name"].lower() == product_name.lower():
                return prod
        return None

    def update_product_quantity(self, product_name, new_quantity):
        product = self._get_product_by_name(product_name)
        if product:
            old_quantity = product["quantity"]
            product["quantity"] = new_quantity
            self.audit_log.log_event(
                "ProductQuantityUpdated",
                {"product_name": product_name, "old_quantity": old_quantity, "new_quantity": new_quantity, "status": "success"}
            )
            print(f"Product '{product_name}' quantity updated from {old_quantity} to {new_quantity}.")
            return True
        self.audit_log.log_event("ProductQuantityUpdated", {"product_name": product_name, "new_quantity": new_quantity, "status": "failed", "reason": "not found"})
        print(f"Error: Product '{product_name}' not found for quantity update.")
        return False

    def delete_product(self, product_name):
        product_id_to_delete = None
        for prod_id, prod_data in self.products.items():
            if prod_data["name"].lower() == product_name.lower():
                product_id_to_delete = prod_id
                break

        if product_id_to_delete:
            deleted_product = self.products.pop(product_id_to_delete)
            self.audit_log.log_event(
                "ProductDeleted",
                {"product_name": product_name, "product_id": deleted_product["id"], "status": "success"}
            )
            print(f"Product '{product_name}' (ID: {deleted_product['id']}) has been DELETED.")
            return True
        self.audit_log.log_event("ProductDeleted", {"product_name": product_name, "status": "failed", "reason": "not found"})
        print(f"Error: Product '{product_name}' not found for deletion.")
        return False

class AIAgent:
    """Simulates an AI agent that processes commands and interacts with the ProductService."""
    def __init__(self, product_service, audit_log):
        self.product_service = product_service
        self.audit_log = audit_log

    def process_command(self, command):
        self.audit_log.log_event("AgentCommandReceived", {"command": command})
        print(f"\n[AGENT] Processing command: '{command}'")

        # Simple command parsing (simulating AI's interpretation)
        if "update quantity for product" in command.lower():
            parts = command.lower().split(" ")
            try:
                product_name_index = parts.index("product") + 1
                quantity_index = parts.index("to") + 1
                product_name = parts[product_name_index].strip("'")
                new_quantity = int(parts[quantity_index])
                self.product_service.update_product_quantity(product_name, new_quantity)
            except (ValueError, IndexError):
                print(f"[AGENT] Could not parse update quantity command: {command}")
                self.audit_log.log_event("AgentCommandFailed", {"command": command, "reason": "parsing error"})
        elif "clear stock for product" in command.lower():
            # --- THIS IS THE CRITICAL PART DEMONSTRATING THE ARTICLE'S POINT ---
            # Simulating a flawed AI interpretation:
            # The intent might be to set quantity to 0, but due to a bug/misinterpretation,
            # the agent decides to DELETE the product instead.
            parts = command.lower().split("for product")
            try:
                product_name = parts[1].strip().strip("'")
                print(f"[AGENT] Interpreting 'clear stock for product {product_name}' as a DELETE operation due to flawed logic.")
                # The audit log records the *decision* of the agent, but does not *prevent* the subsequent API call.
                self.audit_log.log_event(
                    "AgentDecision",
                    {"command_intent": command, "interpreted_action": "delete_product", "product": product_name, "warning": "Potential misinterpretation leading to unintended action"}
                )
                self.product_service.delete_product(product_name) # This is the "bad" API call
                # The audit log for ProductDeleted will be created by ProductService *after* the deletion.
            except (ValueError, IndexError):
                print(f"[AGENT] Could not parse clear stock command: {command}")
                self.audit_log.log_event("AgentCommandFailed", {"command": command, "reason": "parsing error"})
        else:
            print(f"[AGENT] Unknown command: {command}")
            self.audit_log.log_event("AgentCommandFailed", {"command": command, "reason": "unknown command"})

# --- Main execution --- 
if __name__ == "__main__":
    audit_manager = AuditLog()
    product_api = ProductService(audit_manager)
    ai_agent = AIAgent(product_api, audit_manager)

    print("--- Initial Product Inventory ---")
    print(json.dumps(product_api.products, indent=2))

    # Scenario 1: Agent makes a good, intended API call
    print("\n--- Scenario 1: Agent performs an intended update ---")
    ai_agent.process_command("Update quantity for product 'Laptop' to 80")
    print("\n--- Current Product Inventory after Scenario 1 ---")
    print(json.dumps(product_api.products, indent=2))

    # Scenario 2: Agent makes a "bad" API call due to flawed interpretation
    # This demonstrates the core problem: audit logs record *after* the fact.
    print("\n--- Scenario 2: Agent makes a BAD API call due to flawed logic ---")
    ai_agent.process_command("Clear stock for product 'Tablet'")
    # The audit log will show the agent's decision and then the product deletion.
    # But the deletion itself was not prevented by the audit log.
    print("\n--- Current Product Inventory after Scenario 2 ---")
    print(json.dumps(product_api.products, indent=2))

    # Scenario 3: Agent tries to update a deleted product (will fail)
    print("\n--- Scenario 3: Agent tries to update a deleted product ---")
    ai_agent.process_command("Update quantity for product 'Tablet' to 10")
    print("\n--- Current Product Inventory after Scenario 3 ---")
    print(json.dumps(product_api.products, indent=2))

    print("\n--- All Audit Logs ---")
    for log in audit_manager.get_logs():
        print(json.dumps(log))

    print("\n--- Summary of the problem ---")
    print("The 'Clear stock for product 'Tablet'' command led to a 'ProductDeleted' event.")
    print("The audit log recorded this action, but it did not *prevent* the deletion.")
    print("This illustrates how audit logs are reactive (record what happened) rather than proactive (preventing bad actions).")
