# backend/app/services/calculation.py
from typing import Dict, List
from app.models import Session
from app.schemas import TransactionCreate


def calculate_shares(session: Session) -> Dict[int, float]:
    """
    Calculate each participant's share of the bill.

    Returns:
        {participant_id: total_owed}
    """
    if not session.participants:
        return {}

    shares = {p.id: 0.0 for p in session.participants}

    for item in session.items:
        if not item.assignments:
            # Unassigned - split equally among all
            split_amount = item.amount / len(session.participants)
            for p in session.participants:
                shares[p.id] += split_amount
            continue

        # Calculate based on assignments
        total_assigned_percent = sum(a.share_percent for a in item.assignments)

        for assignment in item.assignments:
            if assignment.fixed_amount:
                amount = assignment.fixed_amount
            else:
                # Proportional split
                if total_assigned_percent > 0:
                    amount = (assignment.share_percent / total_assigned_percent) * item.amount
                else:
                    amount = 0

            shares[assignment.participant_id] += amount

    # Add tax and tip proportionally to each person's subtotal
    subtotal = sum(shares.values())
    if subtotal > 0:
        tax_tip_ratio = (session.tax_amount + session.tip_amount) / subtotal
        for pid in shares:
            shares[pid] *= (1 + tax_tip_ratio)

    # Round to 2 decimal places
    return {k: round(v, 2) for k, v in shares.items()}


def calculate_settlement(shares: Dict[int, float]) -> List[TransactionCreate]:
    """
    Calculate optimal settlement transactions.

    Net out mutual debts to minimize number of transactions.

    Returns:
        List of TransactionCreate objects
    """
    # Calculate net balance for each participant
    # Positive = owes money (debtor)
    # Negative = is owed money (creditor)
    total = sum(shares.values())
    average = total / len(shares) if shares else 0

    net_balances = {pid: amount - average for pid, amount in shares.items()}

    # Separate debtors and creditors
    debtors = []  # (id, amount_owed)
    creditors = []  # (id, amount_owed) [positive = owed to them]

    for pid, balance in net_balances.items():
        if balance > 0.01:  # Owes money
            debtors.append((pid, balance))
        elif balance < -0.01:  # Is owed money
            creditors.append((pid, -balance))

    # Sort by amount (largest first for efficiency)
    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    transactions = []

    while debtors and creditors:
        debtor_id, debt_amount = debtors[0]
        creditor_id, credit_amount = creditors[0]

        transfer_amount = min(debt_amount, credit_amount)

        if transfer_amount > 0.01:  # Only create transaction if meaningful amount
            transactions.append(TransactionCreate(
                payer_id=debtor_id,
                payee_id=creditor_id,
                amount=round(transfer_amount, 2)
            ))

        # Update remaining amounts
        debtors[0] = (debtor_id, debt_amount - transfer_amount)
        creditors[0] = (creditor_id, credit_amount - transfer_amount)

        # Remove if settled
        if debtors[0][1] < 0.01:
            debtors.pop(0)
        if creditors[0][1] < 0.01:
            creditors.pop(0)

    return transactions


def calculate_item_split(item_amount: float, assignments: list) -> Dict[int, float]:
    """
    Calculate how much each participant owes for a specific item.

    Args:
        item_amount: Total item cost
        assignments: List of Assignment objects for this item

    Returns:
        {participant_id: amount_owed_for_item}
    """
    if not assignments:
        return {}

    total_percent = sum(a.share_percent for a in assignments)
    if total_percent == 0:
        return {}

    splits = {}
    for assignment in assignments:
        if assignment.fixed_amount:
            splits[assignment.participant_id] = assignment.fixed_amount
        else:
            amount = (assignment.share_percent / total_percent) * item_amount
            splits[assignment.participant_id] = round(amount, 2)

    return splits
