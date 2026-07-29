"""
cv_schema.py - Modèles Pydantic pour la validation du schéma JSON de CV
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class CompetenceCategory(BaseModel):
    """Représente un groupe de compétences par catégorie (ex: Langages, Outils, Frameworks)."""
    model_config = {"extra": "forbid"}

    categorie: str = Field(..., description="Nom de la catégorie de compétences (ex: 'Langages', 'Outils')")
    items: List[str] = Field(default_factory=list, description="Liste des compétences dans cette catégorie")


class Experience(BaseModel):
    """Représente une expérience professionnelle."""
    model_config = {"extra": "forbid"}

    poste: str = Field(..., description="Intitulé du poste occupé")
    entreprise: Optional[str] = Field(None, description="Nom de l'entreprise ou organisation")
    dates: Optional[str] = Field(None, description="Période ou dates (ex: '2022 - Présent', '2020 - 2022')")
    bullets: List[str] = Field(default_factory=list, description="Points clés, réalisations ou missions")


class Formation(BaseModel):
    """Représente un diplôme ou un parcours de formation."""
    model_config = {"extra": "forbid"}

    diplome: str = Field(..., description="Intitulé du diplôme ou de la formation")
    etablissement: Optional[str] = Field(None, description="Nom de l'établissement ou école")
    date: Optional[str] = Field(None, description="Année ou période d'obtention (ex: '2021', '2018 - 2021')")


class CVData(BaseModel):
    """Schéma principal rassemblant toutes les sections d'un CV."""
    model_config = {"extra": "forbid"}

    name: str = Field(..., description="Nom complet du candidat")
    title: Optional[str] = Field(None, description="Titre ou poste recherché / actuel")
    contact: List[str] = Field(default_factory=list, description="Informations de contact (email, téléphone, localisation, etc.)")
    profil: Optional[str] = Field(None, description="Accroche ou résumé du profil professionnel (3-4 lignes)")
    savoir_etre: List[str] = Field(default_factory=list, description="Qualités personnelles / soft skills")
    competences: List[CompetenceCategory] = Field(default_factory=list, description="Compétences techniques regroupées par catégories")
    langues: List[str] = Field(default_factory=list, description="Langues parlées avec niveau (ex: 'Français (natif)', 'Anglais (courant)')")
    experiences: List[Experience] = Field(default_factory=list, description="Liste des expériences professionnelles")
    formation: List[Formation] = Field(default_factory=list, description="Liste des formations et diplômes")
