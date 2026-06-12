from datetime import date

DAILY_QUESTIONS_EN = [
    "What are the total sales by state?",
    "Show the top 10 products by revenue.",
    "Which category has the highest profit?",
    "What is the monthly sales trend?",
    "Compare revenue across all regions.",
    "Show a pie chart of sales by category.",
    "What is the average order value by customer segment?",
    "Which state had the lowest sales last year?",
    "Show the top 5 customers by total purchase value.",
    "What is the total profit margin across all products?",
    "Plot the yearly revenue trend.",
    "Which product subcategory is most profitable?",
    "What percentage of total sales comes from each region?",
    "Show me sales performance by ship mode.",
    "What is the total number of orders per year?",
    "Which city generates the most revenue?",
    "Show the distribution of order quantities.",
    "Compare average discount by product category.",
    "What are the top 10 cities by number of orders?",
    "Show monthly profit trend for all years.",
    "Which segment (Consumer/Corporate/Home Office) buys the most?",
    "What is the correlation between discount and profit?",
    "Show me the worst performing products by profit.",
    "What is the average shipping time by region?",
    "Which products are sold at a loss?",
    "Show sales growth rate year over year.",
    "What is the total revenue from technology products?",
    "Which month historically has the highest sales?",
    "Compare profit margins between categories.",
    "Show the top 10 most returned product categories.",
]
DAILY_QUESTIONS_FR = [
    "Quelles sont les ventes totales par État ?",
"Affichez les 10 produits les plus performants en termes de chiffre d'affaires.",
"Quelle catégorie possède la marge bénéficiaire la plus élevée ?",
"Quelle est la tendance mensuelle des ventes ?",
"Comparez le chiffre d'affaires entre toutes les régions.",
"Affichez un diagramme en secteurs des ventes par catégorie.",
"Quelle est la valeur moyenne de commande par segment de clientèle ?",
"Quel État a enregistré les ventes les plus faibles l'année dernière ?",
"Affichez les 5 principaux clients par valeur d'achat totale.",
"Quelle est la marge bénéficiaire totale sur l'ensemble des produits ?",
"Tracez la tendance annuelle du chiffre d'affaires.",
"Quelle sous-catégorie de produit est la plus rentable ?",
"Quel pourcentage des ventes totales provient de chaque région ?",
"Montrez-moi les performances de vente par mode d'expédition.",
"Quel est le nombre total de commandes par an ?",
"Quelle ville génère le plus de chiffre d'affaires ?",
"Affichez la distribution des quantités commandées.",
"Comparez la remise moyenne par catégorie de produit.",
"Quelles sont les 10 villes principales par nombre de commandes ?",
"Affichez la tendance mensuelle du profit pour toutes les années.",
"Quel segment (Consommateur/Entreprise/Bureau à domicile) achète le plus ?",
"Quelle est la corrélation entre remise et profit ?",
"Montrez-moi les produits les moins performants en termes de profit.",
"Quel est le temps moyen d'expédition par région ?",
"Quels produits sont vendus à perte ?",
"Affichez le taux de croissance des ventes d'une année sur l'autre.",
"Quel est le chiffre d'affaires total des produits technologiques ?",
"Quel mois a historiquement les ventes les plus élevées ?",
"Comparez les marges bénéficiaires entre les catégories.",
"Affichez les 10 catégories de produits les plus retournées."
]


def get_daily_question(lang="en"):
    """
    Proposes an automatique question each day.
    """
    today      = date.today()
    # Gets the day number from the year days
    day_number = today.timetuple().tm_yday
    if lang == 'fr':
        questions = DAILY_QUESTIONS_FR
    else:
        questions = DAILY_QUESTIONS_EN
    # We used modulo to loop through the index 
    # even if we passed the questions length
    index      = day_number % len(questions)
    question   = questions[index]

    if lang == 'fr':
        label = f"Question du jour - {today.strftime('%d/%m/%Y')}"
    else:
        label = f"Daily Insight - {today.strftime('%B %d, %Y')}"
    
    return {
        "question":   question,
        "label":      label,
        "day_number": day_number,
        "index":      index,
        "total":      len(questions),
        "date":       today.isoformat(),
    }