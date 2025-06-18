from .llm_config import gpt4
from langchain.schema import HumanMessage

def appel_llm(fiche):
    """
    Prend une instance FicheConsultation et retourne un diagnostic IA sous forme de texte.
    """
    prompt = (
        f"Patient : {fiche.nom} {fiche.prenom}, {fiche.age} ans\n"
        f"Motif de consultation : {fiche.motif_consultation}\n"
        f"Histoire de la maladie : {fiche.histoire_maladie}\n"
        f"Signes vitaux : Température {fiche.temperature}°C, SpO2 {fiche.spo2}%, "
        f"Tension artérielle {fiche.tension_arterielle}, Pouls {fiche.pouls}/min\n"
        f"Antécédents : {fiche.autres_antecedents}\n"
        f"Plaintes : Céphalées={fiche.cephalees}, Vertiges={fiche.vertiges}, Palpitations={fiche.palpitations}\n"
        f"Examen clinique : {fiche.etat}\n"
        "Donne un diagnostic différentiel, examens complémentaires, traitement, conseils."
    )
    message = HumanMessage(content=prompt)
    result = gpt4.invoke([message])
    return result.content