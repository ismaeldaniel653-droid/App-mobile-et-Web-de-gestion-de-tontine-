def calculer_contribution_reserve(montant_encaisse, pourcentage_reserve):
    """Calcule la contribution vers la caisse de réserve."""
    if montant_encaisse < 0:
        raise ValueError("Le montant encaissé ne peut pas être négatif.")
    if pourcentage_reserve < 0:
        raise ValueError("Le pourcentage de réserve ne peut pas être négatif.")
    return int((montant_encaisse * pourcentage_reserve) / 100)


def calculer_couverture(montant_manquant, solde_reserve, membres, mode_repartition):
    """Calcule la répartition du manque après usage de la réserve."""
    if montant_manquant < 0:
        raise ValueError("Le montant manquant ne peut pas être négatif.")
    if solde_reserve < 0:
        raise ValueError("Le solde de réserve ne peut pas être négatif.")
    if not membres:
        return []

    montant_a_couvrir = max(0, montant_manquant - min(solde_reserve, montant_manquant))
    if montant_a_couvrir == 0:
        return [0 for _ in membres]

    if mode_repartition == "selon_mains":
        total_mains = sum(membres)
        if total_mains == 0:
            return [0 for _ in membres]
        parts = []
        for index, mains in enumerate(membres):
            part = (montant_a_couvrir * mains) // total_mains
            parts.append(part)
        reste = montant_a_couvrir - sum(parts)
        for index in range(reste):
            parts[index] += 1
        return parts

    if mode_repartition != "egal":
        raise ValueError("Mode de répartition inconnu.")

    base = montant_a_couvrir // len(membres)
    reste = montant_a_couvrir % len(membres)
    return [base + (1 if i < reste else 0) for i in range(len(membres))]


# note: cette fonction est volontairement légère et pure; la logique de service métier
# complète pourra être ajoutée ensuite dans une couche plus poussée si besoin.
