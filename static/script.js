
const form = document.getElementById("scrape-form");
const urlInput = document.getElementById("url-input");
const scrapeButton = document.getElementById("scrape-button");
const exportButton = document.getElementById("export-button");
const message = document.getElementById("message");
const resultsSection = document.getElementById("results-section");
const resultsDescription = document.getElementById("results-description");
const productGrid = document.getElementById("product-grid");
const analyzePageButton = document.getElementById("analyze-page-button");
const aiMessage = document.getElementById("ai-message");
const aiResults = document.getElementById("ai-results");

let derniersProduits = [];


function afficherMessage(texte, estErreur = false) {
    message.textContent = texte;
    message.classList.toggle("error", estErreur);
    message.hidden = false;
}


function masquerMessage() {
    message.textContent = "";
    message.classList.remove("error");
    message.hidden = true;
}


function creerCarteProduit(produit) {
    const carte = document.createElement("article");
    carte.className = "product-card";

    const zoneImage = document.createElement("div");
    zoneImage.className = "product-image-wrap";

    if (produit.image_url) {
        const image = document.createElement("img");
        image.className = "product-image";
        image.src = produit.image_url;
        image.alt = produit.titre || "Image du produit";
        image.loading = "lazy";

        image.addEventListener("error", () => {
            image.remove();
            const placeholder = document.createElement("span");
            placeholder.className = "image-placeholder";
            placeholder.textContent = "Image indisponible";
            zoneImage.appendChild(placeholder);
        }, { once: true });

        zoneImage.appendChild(image);
    } else {
        const placeholder = document.createElement("span");
        placeholder.className = "image-placeholder";
        placeholder.textContent = "Aucune image";
        zoneImage.appendChild(placeholder);
    }

    const informations = document.createElement("div");
    informations.className = "product-info";

    const titre = document.createElement("h3");
    titre.className = "product-title";
    titre.textContent = produit.titre || "Titre indisponible";

    const prix = document.createElement("p");
    prix.className = "product-price";

    if (typeof produit.prix === "number") {
        prix.textContent = `${produit.prix.toFixed(2)} ${produit.devise || ""}`.trim();
    } else {
        prix.textContent = "Prix indisponible";
    }

    informations.append(titre, prix);
    carte.append(zoneImage, informations);

    return carte;
}


function afficherProduits(produits) {
    productGrid.replaceChildren();

    const fragment = document.createDocumentFragment();

    produits.forEach((produit) => {
        fragment.appendChild(creerCarteProduit(produit));
    });

    productGrid.appendChild(fragment);
    resultsSection.hidden = false;
    resultsDescription.textContent =
        `${produits.length} produit(s) récupéré(s).`;
}


form.addEventListener("submit", async (evenement) => {
    evenement.preventDefault();
    masquerMessage();

    const url = urlInput.value.trim();

    if (!url) {
        afficherMessage("Veuillez saisir une URL.", true);
        return;
    }

    scrapeButton.disabled = true;
    exportButton.disabled = true;
    scrapeButton.textContent = "Scraping en cours…";
    afficherMessage("Connexion au site et extraction des données…");

    try {
        const reponse = await fetch(
            `/api/scrape?url=${encodeURIComponent(url)}`
        );

        const resultat = await reponse.json();

        if (!reponse.ok || !resultat.success) {
            const erreur = resultat.error?.message
                || "Une erreur est survenue pendant le scraping.";

            throw new Error(erreur);
        }

        derniersProduits = resultat.data || [];
        afficherProduits(derniersProduits);

        afficherMessage(
            `Extraction terminée : ${derniersProduits.length} produit(s) récupéré(s).`
        );

        exportButton.disabled = derniersProduits.length === 0;
    } catch (erreur) {
        derniersProduits = [];
        exportButton.disabled = true;
        afficherMessage(
            erreur.message || "Impossible de contacter l'API.",
            true
        );
    } finally {
        scrapeButton.disabled = false;
        scrapeButton.textContent = "Lancer le scraping";
    }
});


exportButton.addEventListener("click", () => {
    if (derniersProduits.length === 0) {
        afficherMessage("Aucun produit à exporter.", true);
        return;
    }

    const colonnes = ["titre", "prix", "devise", "image_url"];

    function echapperCSV(valeur) {
        let texte = valeur === null || valeur === undefined
            ? ""
            : String(valeur);

        if (/^[\s]*[=+@\-\t\r]/.test(texte)) {
            texte = `'${texte}`;
        }

        return `"${texte.replace(/"/g, '""')}"`;
    }

    const lignes = [
        colonnes.map(echapperCSV).join(","),
        ...derniersProduits.map((produit) =>
            colonnes.map((colonne) => echapperCSV(produit[colonne])).join(",")
        )
    ];

    const contenu = "\uFEFF" + lignes.join("\r\n");
    const fichier = new Blob([contenu], {
        type: "text/csv;charset=utf-8;"
    });

    const lien = document.createElement("a");
    const urlFichier = URL.createObjectURL(fichier);

    lien.href = urlFichier;
    lien.download = "produits.csv";
    document.body.appendChild(lien);
    lien.click();
    lien.remove();

    URL.revokeObjectURL(urlFichier);
});


analyzePageButton.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    aiResults.hidden = true;
    aiMessage.hidden = false;
    aiMessage.classList.remove("error");

    if (!url) {
        aiMessage.textContent = "Saisissez d’abord l’URL de la page.";
        aiMessage.classList.add("error");
        return;
    }

    analyzePageButton.disabled = true;
    analyzePageButton.textContent = "Analyse en cours…";
    aiMessage.textContent = "Le texte de la page est envoyé au service IA pour analyse…";

    try {
        const reponse = await fetch("/api/analyze-page", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });
        const resultat = await reponse.json();
        if (!reponse.ok || !resultat.success) {
            throw new Error(resultat.error?.message || "L’analyse IA a échoué.");
        }

        const analyse = resultat.data;
        document.getElementById("ai-category").textContent = analyse.category;
        document.getElementById("ai-summary").textContent = analyse.summary;
        document.getElementById("ai-name").textContent = analyse.name || "Non trouvé";
        document.getElementById("ai-description").textContent = analyse.description || "Non trouvée";
        const liste = document.getElementById("ai-features");
        liste.replaceChildren();
        for (const caracteristique of analyse.features) {
            const item = document.createElement("li");
            item.textContent = caracteristique;
            liste.appendChild(item);
        }
        aiResults.hidden = false;
        aiMessage.textContent = "Analyse terminée.";
    } catch (erreur) {
        aiMessage.textContent = erreur instanceof TypeError
            ? "Impossible de contacter le serveur local."
            : (erreur.message || "L’analyse IA a échoué.");
        aiMessage.classList.add("error");
    } finally {
        analyzePageButton.disabled = false;
        analyzePageButton.textContent = "Analyser avec l’IA";
    }
});
