
"use strict";

// =========================================================
// UNIFUNL — Vérificateur de liens cassés
// Gestion du formulaire, des résultats et de l'export CSV
// =========================================================

const formulaire = document.getElementById("link-form");
const champUrl = document.getElementById("url");
const selectMaxLiens = document.getElementById("max-links");
const bouton = document.getElementById("submit-button");
const message = document.getElementById("message");
const sectionResultats = document.getElementById("results");
const corpsTableau = document.getElementById("results-body");
const boutonExport = document.getElementById("export-csv");

let dernierRapport = null;
let controleEnCours = false;

// Affiche un message de succès, d'erreur ou d'information.
function afficherMessage(texte, type = "") {
    message.textContent = texte;
    message.className = `message ${type}`.trim();
}

// Efface le message affiché précédemment.
function effacerMessage() {
    afficherMessage("");
}

// Valide l'URL avant d'envoyer la requête au serveur.
function validerUrl(url) {
    if (!url) {
        return "Veuillez saisir l'adresse du site à analyser.";
    }

    try {
        const adresse = new URL(url);

        if (!["http:", "https:"].includes(adresse.protocol)) {
            return "L'adresse doit commencer par http:// ou https://.";
        }

        if (!adresse.hostname || !adresse.hostname.includes(".")) {
            return "Veuillez saisir une adresse de site valide, par exemple https://books.toscrape.com.";
        }

        return null;
    } catch {
        return "L'adresse saisie est invalide. Exemple : https://books.toscrape.com";
    }
}

// Ajoute une cellule au tableau en utilisant du texte non interprété comme HTML.
function ajouterCellule(ligne, contenu) {
    const cellule = document.createElement("td");
    cellule.textContent = contenu ?? "—";
    ligne.appendChild(cellule);
    return cellule;
}

// Affiche le rapport reçu de l'API.
function afficherResultats(rapport) {
    document.getElementById("found-count").textContent =
        rapport.nombre_liens_trouves;

    document.getElementById("checked-count").textContent =
        rapport.nombre_liens_verifies;

    document.getElementById("broken-count").textContent =
        rapport.nombre_liens_casses;

    document.getElementById("error-count").textContent =
        rapport.nombre_erreurs_reseau;

    corpsTableau.replaceChildren();

    for (const resultat of rapport.resultats) {
        const ligne = document.createElement("tr");

        const celluleUrl = ajouterCellule(ligne, "");
        const lien = document.createElement("a");

        lien.href = resultat.url;
        lien.textContent = resultat.url;
        lien.target = "_blank";
        lien.rel = "noopener noreferrer";

        celluleUrl.appendChild(lien);

        ajouterCellule(
            ligne,
            resultat.status_code === null
                ? "—"
                : String(resultat.status_code)
        );

        const celluleStatut = ajouterCellule(ligne, "");
        const badge = document.createElement("span");

        // Les classes correspondent aux styles du fichier CSS.
        badge.className = `status-badge ${resultat.status}`;
        badge.textContent = {
            ok: "Valide",
            broken: "Cassé",
            error: "Erreur réseau"
        }[resultat.status] ?? resultat.status;

        celluleStatut.appendChild(badge);

        ajouterCellule(ligne, resultat.erreur || "—");
        corpsTableau.appendChild(ligne);
    }

    sectionResultats.hidden = false;
}

// Efface les anciens messages quand l'utilisateur modifie le formulaire.
champUrl.addEventListener("input", () => {
    if (!controleEnCours) {
        effacerMessage();
    }
});

selectMaxLiens.addEventListener("change", () => {
    if (!controleEnCours) {
        effacerMessage();
    }
});

// Vérifie les liens lorsque le formulaire est envoyé.
formulaire.addEventListener("submit", async (evenement) => {
    evenement.preventDefault();

    if (controleEnCours) {
        return;
    }

    const url = champUrl.value.trim();
    const maxLiens = Number(selectMaxLiens.value);

    // Validation explicite avec un message compréhensible.
    const erreurUrl = validerUrl(url);

    if (erreurUrl) {
        afficherMessage(erreurUrl, "error");
        champUrl.focus();
        return;
    }

    if (!Number.isInteger(maxLiens) || maxLiens < 1 || maxLiens > 500) {
        afficherMessage(
            "Le nombre de liens doit être compris entre 1 et 500.",
            "error"
        );
        selectMaxLiens.focus();
        return;
    }

    controleEnCours = true;
    bouton.disabled = true;
    bouton.textContent = "Vérification en cours…";
    sectionResultats.hidden = true;

    afficherMessage(
        "Analyse en cours. La durée dépend du nombre de liens à vérifier.",
        ""
    );

    try {
        const reponse = await fetch("/api/check-links", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url,
                max_liens: maxLiens
            })
        });

        let donnees;

        try {
            donnees = await reponse.json();
        } catch {
            throw new Error(
                "Le serveur a renvoyé une réponse illisible. Réessayez plus tard."
            );
        }

        if (!reponse.ok || !donnees.success) {
            const codeErreur = donnees.error?.code;

            const messagesParCode = {
                MISSING_URL: "Veuillez saisir l'adresse du site à analyser.",
                INVALID_URL: "L'adresse saisie est invalide. Vérifiez son format.",
                INVALID_MAX_LINKS: "Le nombre de liens doit être compris entre 1 et 500.",
                LINK_CHECK_REQUEST_ERROR: "Impossible de récupérer la page. Vérifiez l'adresse et votre connexion.",
                INTERNAL_ERROR: "Une erreur interne est survenue. Réessayez plus tard."
            };

            throw new Error(
                messagesParCode[codeErreur] ||
                donnees.error?.message ||
                "La vérification n'a pas pu être effectuée."
            );
        }

        dernierRapport = donnees.data;
        afficherResultats(dernierRapport);

        afficherMessage(
            `Analyse terminée : ${dernierRapport.nombre_liens_verifies} lien(s) vérifié(s).`,
            "success"
        );
    } catch (erreur) {
        if (erreur instanceof TypeError) {
            afficherMessage(
                "Impossible de contacter le serveur. Vérifiez que l'application Flask est démarrée et réessayez.",
                "error"
            );
        } else {
            afficherMessage(
                erreur.message || "Une erreur inattendue est survenue.",
                "error"
            );
        }
    } finally {
        controleEnCours = false;
        bouton.disabled = false;
        bouton.textContent = "Vérifier les liens";
    }
});

// Exporte les résultats du dernier rapport au format CSV.
boutonExport.addEventListener("click", () => {
    if (!dernierRapport || !dernierRapport.resultats.length) {
        afficherMessage(
            "Aucun résultat à exporter. Lancez d'abord une analyse.",
            "error"
        );
        return;
    }

    const colonnes = [
        "url",
        "status_code",
        "status",
        "url_finale",
        "erreur"
    ];

    const echapperCSV = (valeur) => {
        let texte = valeur == null ? "" : String(valeur);
        if (/^[\s]*[=+@\-\t\r]/.test(texte)) {
            texte = `'${texte}`;
        }
        return `"${texte.replace(/"/g, '""')}"`;
    };

    const lignes = [
        colonnes.map(echapperCSV).join(";"),
        ...dernierRapport.resultats.map((resultat) =>
            colonnes.map((colonne) =>
                echapperCSV(resultat[colonne])
            ).join(";")
        )
    ];

    const contenu = "\uFEFF" + lignes.join("\r\n");
    const blob = new Blob([contenu], {
        type: "text/csv;charset=utf-8;"
    });

    const urlFichier = URL.createObjectURL(blob);
    const lien = document.createElement("a");

    lien.href = urlFichier;
    lien.download = "rapport_liens.csv";
    document.body.appendChild(lien);
    lien.click();
    lien.remove();

    URL.revokeObjectURL(urlFichier);
});
