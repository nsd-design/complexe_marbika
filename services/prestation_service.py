from django.utils import timezone

from salon.models import DetailRepartitionMontant


def get_unique_prestataire(prestations):
    """
    Retourne l'unique prestataire si un seul est impliqueé dans toutes les prestations
    sinon None
    :param prestations:
    :return:
    """

    prestataires = []

    for prestation in prestations:
        prestataires.extend(list(prestation.fait_par.all().values_list('id', flat=True)))

    unique_ids = set(prestataires)

    if len(unique_ids) == 1:
        return unique_ids.pop()

    return None


def attribuer_montant_total(init_prestation_id, employe_id, user, list_services):
    """
    Attributer le montant de la prestation a un seul prestataire
    :param init_prestation:
    :param employe_id:
    :param user:
    :return:
    """

    from salon.models import RepartitionMontantPrestation, Employe, InitPrestation

    employee = Employe.objects.get(id=employe_id)
    init_prestation = InitPrestation.objects.get(id=init_prestation_id)

    montant = init_prestation.montant_total - init_prestation.remise

    rep = None
    if montant > 0:
        rep = RepartitionMontantPrestation.objects.create(
            init_prestation=init_prestation,
            employe=employee,
            montant_attribue=montant,
            created_by=user
        )

        init_prestation.montant_attribue = True
        init_prestation.updated_by = user
        init_prestation.updated_at = timezone.now()
        init_prestation.save()

    if rep:
        for service in list_services:
            DetailRepartitionMontant.objects.create(
                repartition=rep,
                service=service,
                created_by=user
            )