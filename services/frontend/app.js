const API = {
  livres: "http://localhost:8001/api",
  utilisateurs: "http://localhost:8002/api",
  emprunts: "http://localhost:8003/api",
  statistiques: "http://localhost:8004/api",
  recommandations: "http://localhost:8005",
};

const ADMIN_LINKS = [
  { label: "Admin Utilisateurs", href: "http://localhost:8002/admin/", text: "Comptes, rôles et permissions." },
  { label: "Admin Livres", href: "http://localhost:8001/admin/", text: "Catalogue et requêtes de livres." },
  { label: "Admin Emprunts", href: "http://localhost:8003/admin/", text: "Historique, retards et retours." },
];

const SESSION_KEY = "dit-librairie-session";
const PAGE = document.body.dataset.page;
const PIE_COLORS = ["#1b5a68", "#356a77", "#6d8890", "#a9b8bc", "#d7dedd", "#87a2aa"];

document.addEventListener("DOMContentLoaded", () => {
  renderHeader();
  routePage();
});

function routePage() {
  if (PAGE === "home") {
    initHomePage().catch(handleError);
  } else if (PAGE === "books") {
    initBooksPage().catch(handleError);
  } else if (PAGE === "login") {
    initLoginPage();
  } else if (PAGE === "register") {
    initRegisterPage().catch(handleError);
  } else if (PAGE === "account") {
    initAccountPage().catch(handleError);
  }
}

function getSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
  } catch (_error) {
    return null;
  }
}

function setSession(utilisateur) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(utilisateur));
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

function authHeaders() {
  const session = getSession();
  if (!session) {
    return {};
  }
  return {
    "X-User-Id": String(session.id),
    "X-User-Role": session.type_utilisateur,
    "X-User-Name": session.nom_complet || `${session.prenom} ${session.nom}`.trim(),
  };
}

async function apiFetch(url, options = {}) {
  const headers = { ...authHeaders(), ...(options.headers || {}) };
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, { ...options, headers });
  const contentType = response.headers.get("Content-Type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "string" ? formatErrorText(payload) : payload.detail || JSON.stringify(payload);
    throw new Error(detail || "Erreur serveur");
  }

  return payload;
}

function showToast(message) {
  const toast = document.getElementById("toast");
  if (!toast) {
    return;
  }
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 2800);
}

function handleError(error) {
  showToast(error.message || "Une erreur est survenue.");
}

function renderHeader() {
  const session = getSession();
  const header = document.getElementById("siteHeader");
  if (!header) {
    return;
  }

  const links = session
    ? [
        { href: "index.html", label: "Accueil", page: "home" },
        { href: "livres.html", label: "Livres", page: "books" },
        { href: "account.html", label: "Mon Compte", page: "account" },
      ]
    : [
        { href: "index.html", label: "Accueil", page: "home" },
        { href: "livres.html", label: "Livres", page: "books" },
        { href: "register.html", label: "Créer un compte", page: "register" },
      ];

  header.className = "site-header";
  header.innerHTML = `
    <div class="site-header-inner">
      <a class="brand" href="index.html">
        <img class="brand-mark" src="assets/dit-logo.svg" alt="Logo DIT" />
        <span class="brand-copy">
          <strong>DIT Librairie</strong>
          <span>Catalogue académique et back-office</span>
        </span>
      </a>
      <nav class="nav-main">
        ${links
          .map(
            (link) => `
              <a href="${link.href}" class="${PAGE === link.page ? "active" : ""}">
                ${link.label}
              </a>
            `
          )
          .join("")}
      </nav>
      <div class="nav-tools">
        ${
          session
            ? `
              <span class="user-chip">
                <span class="role-dot"></span>
                <span>${escapeHtml(session.nom_complet || `${session.prenom} ${session.nom}`)}</span>
                <span>${escapeHtml(roleLabel(session.type_utilisateur))}</span>
              </span>
              <button id="logoutButton" class="btn btn-ghost nav-action" type="button">Déconnexion</button>
            `
            : `
              <a href="login.html" class="btn btn-secondary nav-action">Connexion</a>
            `
        }
      </div>
    </div>
  `;

  const logoutButton = document.getElementById("logoutButton");
  if (logoutButton) {
    logoutButton.addEventListener("click", () => {
      clearSession();
      window.location.href = "index.html";
    });
  }
}

async function initHomePage() {
  const [catalogue, recents] = await Promise.all([
    apiFetch(`${API.livres}/livres/?limite=200`),
    apiFetch(`${API.livres}/livres/recents/?limite=6`),
  ]);

  const countNode = document.getElementById("homeBookCount");
  if (countNode) {
    countNode.textContent = String(catalogue.length);
  }

  renderBookCollection(document.getElementById("homeLatestBooks"), recents);
}

async function initBooksPage() {
  await populateBookCategories();

  const form = document.getElementById("bookSearchForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await runBooksSearch();
  });

  document.getElementById("searchQuery").addEventListener("input", debounce(runBooksSearch, 250));
  document.getElementById("searchCategory").addEventListener("change", runBooksSearch);
  document.getElementById("searchAvailable").addEventListener("change", runBooksSearch);

  await Promise.all([runBooksSearch(), loadBooksSecondarySection()]);
}

async function runBooksSearch() {
  const query = document.getElementById("searchQuery").value.trim();
  const category = document.getElementById("searchCategory").value.trim();
  const available = document.getElementById("searchAvailable").checked;
  const params = new URLSearchParams();
  const resultsSection = document.getElementById("booksResultsSection");

  if (query) {
    params.set("q", query);
  }
  if (category) {
    params.set("categorie", category);
  }
  if (available) {
    params.set("disponible", "true");
  }

  if (!query && !category && !available) {
    resultsSection.style.display = "none";
    document.getElementById("booksResults").innerHTML = "";
    return;
  }

  const url = `${API.livres}/livres/${params.toString() ? `?${params.toString()}` : ""}`;
  const livres = await apiFetch(url);
  resultsSection.style.display = "";
  renderBookCollection(document.getElementById("booksResults"), livres);
}

async function populateBookCategories() {
  const select = document.getElementById("searchCategory");
  if (!select) {
    return;
  }

  const livres = await apiFetch(`${API.livres}/livres/?limite=300`);
  const categories = [...new Set(livres.map((livre) => livre.categorie).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b, "fr")
  );

  select.innerHTML = `
    <option value="">Tous</option>
    ${categories
      .map((categorie) => `<option value="${escapeAttribute(categorie)}">${escapeHtml(categorie)}</option>`)
      .join("")}
  `;
}

async function loadBooksSecondarySection() {
  const session = getSession();
  const eyebrow = document.getElementById("booksSecondaryEyebrow");
  const title = document.getElementById("booksSecondaryTitle");
  const container = document.getElementById("booksSecondaryList");
  const canReceiveRecommendations =
    session && ["etudiant", "professeur"].includes(session.type_utilisateur);

  if (!canReceiveRecommendations) {
    const recents = await apiFetch(`${API.livres}/livres/recents/?limite=6`);
    eyebrow.textContent = "Sélection";
    title.textContent = "Derniers livres ajoutés";
    renderBookCollection(container, recents);
    return;
  }

  const historique = await apiFetch(`${API.emprunts}/emprunts/utilisateur/${session.id}/`);
  if (!historique.length) {
    const recents = await apiFetch(`${API.livres}/livres/recents/?limite=6`);
    eyebrow.textContent = "Sélection";
    title.textContent = "Derniers livres ajoutés";
    renderBookCollection(container, recents);
    return;
  }

  try {
    container.innerHTML = loadingState(
      "Patientez une minute, le temps que les recommandations soient générées."
    );
    const [reponse, catalogue] = await Promise.all([
      apiFetch(`${API.recommandations}/recommendations/${session.id}`),
      apiFetch(`${API.livres}/livres/?limite=200`),
    ]);
    const catalogueParId = new Map(catalogue.map((livre) => [livre.id, livre]));
    const recommandations = (reponse.recommandations || []).map((item) => ({
      ...(catalogueParId.get(item.book_id) || {
        id: item.book_id,
        titre: item.titre,
        auteur: "Catalogue externe",
        categorie: "Suggestion",
        quantite_disponible: 0,
        quantite_totale: 0,
        description: "",
        disponibilite: "Disponible",
      }),
      titre: item.titre,
      recommendationScore: item.score,
    }));

    eyebrow.textContent = "Suggestions";
    title.textContent = "Recommandations pour vous";
    renderBookCollection(container, recommandations, { showScore: true });
  } catch (_error) {
    const recents = await apiFetch(`${API.livres}/livres/recents/?limite=6`);
    eyebrow.textContent = "Sélection";
    title.textContent = "Derniers livres ajoutés";
    renderBookCollection(container, recents);
  }
}

function initLoginPage() {
  const form = document.getElementById("loginForm");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = Object.fromEntries(new FormData(form).entries());
    try {
      const response = await apiFetch(`${API.utilisateurs}/utilisateurs/connexion/`, {
        method: "POST",
        body: JSON.stringify(formData),
      });
      setSession(response.utilisateur);
      showToast("Connexion réussie.");
      window.location.href = "account.html";
    } catch (error) {
      handleError(error);
    }
  });
}

async function initRegisterPage() {
  const roleSelect = document.getElementById("registerRole");
  const roles = await apiFetch(`${API.utilisateurs}/utilisateurs/types/`);
  roleSelect.innerHTML = roles
    .map((role) => `<option value="${role.code}">${escapeHtml(role.libelle)}</option>`)
    .join("");

  const form = document.getElementById("registerForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = Object.fromEntries(new FormData(form).entries());
    try {
      const utilisateur = await apiFetch(`${API.utilisateurs}/utilisateurs/`, {
        method: "POST",
        body: JSON.stringify(formData),
      });
      setSession(utilisateur);
      showToast("Compte créé.");
      window.location.href = "account.html";
    } catch (error) {
      handleError(error);
    }
  });
}

async function initAccountPage() {
  const session = getSession();
  const mount = document.getElementById("accountMount");

  if (!session) {
    mount.innerHTML = `
      <section class="empty-state">
        <h2>Connexion requise</h2>
        <p>Connectez-vous pour accéder à votre espace personnel.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="login.html">Se connecter</a>
          <a class="btn btn-ghost" href="register.html">Créer un compte</a>
        </div>
      </section>
    `;
    return;
  }

  const tabs = getTabsForRole(session.type_utilisateur);
  mount.innerHTML = `
    <div class="account-frame">
      <aside class="account-sidebar">
        <div class="user-chip">
          <span class="role-dot"></span>
          <span>${escapeHtml(session.nom_complet || `${session.prenom} ${session.nom}`)}</span>
        </div>
        <p class="muted">${escapeHtml(roleDescription(session.type_utilisateur))}</p>
        <nav id="tabNav" class="tab-nav">
          ${tabs
            .map(
              (tab, index) => `
                <button class="tab-link ${index === 0 ? "active" : ""}" type="button" data-tab="${tab.id}">
                  <span>${tab.label}</span>
                  <span>${index + 1}</span>
                </button>
              `
            )
            .join("")}
        </nav>
      </aside>
      <section id="tabPanel" class="tab-panel"></section>
    </div>
  `;

  const nav = document.getElementById("tabNav");
  nav.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-tab]");
    if (!button) {
      return;
    }
    nav.querySelectorAll(".tab-link").forEach((node) => node.classList.remove("active"));
    button.classList.add("active");
    try {
      await renderAccountTab(button.dataset.tab);
    } catch (error) {
      handleError(error);
    }
  });

  await renderAccountTab(tabs[0].id);
}

function getTabsForRole(role) {
  if (["etudiant", "professeur"].includes(role)) {
    return [
      { id: "info", label: "Informations" },
      { id: "history", label: "Mon historique" },
      { id: "stats", label: "Stats" },
      { id: "borrow", label: "Emprunter" },
      { id: "requests", label: "Requêtes de livres" },
    ];
  }
  if (role === "gestionnaire") {
    return [
      { id: "info", label: "Informations" },
      { id: "manage-books", label: "Gestion de livres" },
      { id: "manage-requests", label: "Gestion requêtes" },
    ];
  }
  return [
    { id: "info", label: "Informations" },
    { id: "admin-stats", label: "Stats" },
    { id: "admin-tools", label: "Administration" },
  ];
}

async function renderAccountTab(tabId) {
  const panel = document.getElementById("tabPanel");
  if (!panel) {
    return;
  }

  panel.innerHTML = `
    <div class="surface-card">
      <p class="muted">Chargement...</p>
    </div>
  `;

  if (tabId === "info") {
    await renderInfoTab(panel);
    return;
  }
  if (tabId === "history") {
    await renderHistoryTab(panel);
    return;
  }
  if (tabId === "stats") {
    await renderReaderStatsTab(panel);
    return;
  }
  if (tabId === "borrow") {
    await renderBorrowTab(panel);
    return;
  }
  if (tabId === "requests") {
    await renderReaderRequestsTab(panel);
    return;
  }
  if (tabId === "manage-books") {
    await renderManagerBooksTab(panel);
    return;
  }
  if (tabId === "manage-requests") {
    await renderManagerRequestsTab(panel);
    return;
  }
  if (tabId === "admin-stats") {
    await renderAdminStatsTab(panel);
    return;
  }
  if (tabId === "admin-tools") {
    await renderAdminToolsTab(panel);
  }
}

async function renderInfoTab(panel) {
  const session = getSession();
  panel.innerHTML = `
    <div class="panel-header">
      <div>
        <p class="eyebrow">Mon profil</p>
        <h2>Informations du compte</h2>
        <p>Modifiez vos informations de contact et votre mot de passe.</p>
      </div>
    </div>
    <form id="profileForm" class="form-grid">
      <label><span>Prénom</span><input name="prenom" value="${escapeAttribute(session.prenom || "")}" required /></label>
      <label><span>Nom</span><input name="nom" value="${escapeAttribute(session.nom || "")}" required /></label>
      <label><span>Email</span><input name="email" type="email" value="${escapeAttribute(session.email || "")}" required /></label>
      <label><span>Téléphone</span><input name="telephone" value="${escapeAttribute(session.telephone || "")}" /></label>
      <label><span>Département</span><input name="departement" value="${escapeAttribute(session.departement || "")}" /></label>
      <label><span>Numéro de carte</span><input name="numero_carte" value="${escapeAttribute(session.numero_carte || "")}" required /></label>
      <label><span>Rôle</span><input value="${escapeAttribute(roleLabel(session.type_utilisateur))}" disabled /></label>
      <label><span>Nouveau mot de passe</span><input name="mot_de_passe" type="password" placeholder="Laisser vide pour conserver" /></label>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit">Enregistrer</button>
      </div>
    </form>
  `;

  document.getElementById("profileForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    if (!data.mot_de_passe) {
      delete data.mot_de_passe;
    }
    try {
      const updated = await apiFetch(`${API.utilisateurs}/utilisateurs/me/`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
      setSession(updated);
      renderHeader();
      showToast("Profil mis à jour.");
    } catch (error) {
      handleError(error);
    }
  });
}

async function renderHistoryTab(panel) {
  const session = getSession();
  const historique = await apiFetch(`${API.emprunts}/emprunts/utilisateur/${session.id}/`);
  const twelveMonthsAgo = new Date();
  twelveMonthsAgo.setMonth(twelveMonthsAgo.getMonth() - 12);
  const filtered = historique.filter((emprunt) => new Date(emprunt.date_emprunt) >= twelveMonthsAgo);

  panel.innerHTML = `
    <div class="panel-header">
      <div>
        <p class="eyebrow">Traçabilité</p>
        <h2>Mon historique</h2>
        <p>Emprunts et retours des douze derniers mois.</p>
      </div>
    </div>
    ${
      filtered.length
        ? `
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Livre</th>
                  <th>Date d'emprunt</th>
                  <th>Retour prévu</th>
                  <th>Retour effectif</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                ${filtered
                  .map(
                    (emprunt) => `
                      <tr>
                        <td>${escapeHtml(emprunt.livre_titre)}</td>
                        <td>${formatDate(emprunt.date_emprunt)}</td>
                        <td>${formatDate(emprunt.date_retour_prevue)}</td>
                        <td>${emprunt.date_retour_effective ? formatDate(emprunt.date_retour_effective) : "-"}</td>
                        <td><span class="status-pill ${statusClassForLoan(emprunt.statut)}">${escapeHtml(labelForLoanStatus(emprunt.statut))}</span></td>
                      </tr>
                    `
                  )
                  .join("")}
              </tbody>
            </table>
          </div>
        `
        : emptyState("Aucun emprunt sur les douze derniers mois.")
    }
  `;
}

async function renderReaderStatsTab(panel) {
  const session = getSession();
  const [historique, livres] = await Promise.all([
    apiFetch(`${API.emprunts}/emprunts/utilisateur/${session.id}/`),
    apiFetch(`${API.livres}/livres/?limite=300`),
  ]);

  const livresById = new Map(livres.map((livre) => [livre.id, livre]));
  const total = historique.length;
  const durations = historique.map((emprunt) => {
    const start = new Date(emprunt.date_emprunt);
    const end = emprunt.date_retour_effective ? new Date(emprunt.date_retour_effective) : new Date();
    return Math.max(1, Math.round((end - start) / (1000 * 60 * 60 * 24)));
  });
  const moyenne = total ? Math.round(durations.reduce((sum, value) => sum + value, 0) / total) : 0;
  const genres = historique.reduce((acc, emprunt) => {
    const categorie = livresById.get(emprunt.livre_id)?.categorie || "Non classé";
    acc[categorie] = (acc[categorie] || 0) + 1;
    return acc;
  }, {});

  panel.innerHTML = `
    <div class="panel-header">
      <div>
        <p class="eyebrow">Mes usages</p>
        <h2>Stats personnelles</h2>
        <p>Résumé de vos emprunts, durées moyennes et genres les plus consultés.</p>
      </div>
    </div>
    <div class="stat-grid">
      <article class="stat-card"><span>Livres empruntés</span><strong>${total}</strong></article>
      <article class="stat-card"><span>Durée moyenne</span><strong>${moyenne} jours</strong></article>
      <article class="stat-card"><span>Genres différents</span><strong>${Object.keys(genres).length}</strong></article>
    </div>
    <div class="stats-layout">
      <div class="surface-card">
        <h3>Répartition par genre</h3>
        <div class="chart-box"><canvas id="readerGenreChart" width="280" height="280"></canvas></div>
      </div>
      <div class="surface-card">
        <h3>Détail des genres</h3>
        <div class="stack">
          ${Object.entries(genres)
            .sort((a, b) => b[1] - a[1])
            .map(([genre, count], index) => {
              const color = PIE_COLORS[index % PIE_COLORS.length];
              return `
                <div class="status-row">
                  <span class="status-pill" style="background:${color}20;color:${color}">${count}</span>
                  <span>${escapeHtml(genre)}</span>
                </div>
              `;
            })
            .join("") || "<p class='muted'>Aucun genre à afficher.</p>"}
        </div>
      </div>
    </div>
  `;

  drawPieChart(document.getElementById("readerGenreChart"), genres);
}

async function renderBorrowTab(panel) {
  const livres = await apiFetch(`${API.livres}/livres/?limite=200&tri=recents`);
  panel.innerHTML = `
    <div class="panel-header">
      <div>
        <p class="eyebrow">Emprunt</p>
        <h2>Emprunter un livre</h2>
        <p>Choisissez un ouvrage disponible. Les livres sans exemplaire restent visibles mais non empruntables.</p>
      </div>
    </div>
    <div class="surface-card">
      <div class="search-panel">
        <input id="borrowQuery" placeholder="Rechercher un livre..." />
        <input id="borrowCategory" placeholder="Catégorie" />
        <label class="checkline">
          <input id="borrowAvailableOnly" type="checkbox" />
          <span>Disponibles uniquement</span>
        </label>
        <input id="borrowDueDate" type="date" value="${futureDate(14)}" />
      </div>
    </div>
    <div id="borrowResults" class="book-grid"></div>
  `;

  const render = () => {
    const query = document.getElementById("borrowQuery").value.trim().toLowerCase();
    const category = document.getElementById("borrowCategory").value.trim().toLowerCase();
    const availableOnly = document.getElementById("borrowAvailableOnly").checked;
    const filtered = livres.filter((livre) => {
      const matchesQuery =
        !query ||
        [livre.titre, livre.auteur, livre.isbn, livre.categorie].some((value) =>
          String(value || "").toLowerCase().includes(query)
        );
      const matchesCategory = !category || String(livre.categorie || "").toLowerCase().includes(category);
      const matchesAvailable = !availableOnly || livre.quantite_disponible > 0;
      return matchesQuery && matchesCategory && matchesAvailable;
    });

    const html = filtered.map((livre) => borrowCard(livre)).join("") || emptyState("Aucun livre trouvé.");
    document.getElementById("borrowResults").innerHTML = html;
  };

  ["borrowQuery", "borrowCategory", "borrowAvailableOnly"].forEach((id) => {
    document.getElementById(id).addEventListener("input", render);
    document.getElementById(id).addEventListener("change", render);
  });

  document.getElementById("borrowResults").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-borrow-id]");
    if (!button) {
      return;
    }
    const dueDate = document.getElementById("borrowDueDate").value;
    if (!dueDate) {
      showToast("Choisissez une date de retour prévue.");
      return;
    }

    const session = getSession();
    try {
      await apiFetch(`${API.emprunts}/emprunts/`, {
        method: "POST",
        body: JSON.stringify({
          utilisateur_id: session.id,
          livre_id: Number(button.dataset.borrowId),
          date_retour_prevue: dueDate,
          commentaire: "",
        }),
      });
    } catch (error) {
      const message =
        !error?.message || error.message.startsWith("Erreur serveur")
          ? "Emprunt non enregistré."
          : error.message;
      showToast(message);
      return;
    }

    showToast("Emprunt enregistré.");

    try {
      await renderBorrowTab(panel);
    } catch (error) {
      console.error("Rafraîchissement de l'onglet Emprunter impossible après succès:", error);
    }
  });

  render();
}

async function renderReaderRequestsTab(panel) {
  panel.innerHTML = `
    <div class="panel-header">
      <div>
        <p class="eyebrow">Acquisition</p>
        <h2>Requêtes de livres</h2>
        <p>Demandez un ouvrage absent du catalogue. Une vérification est faite avant création.</p>
      </div>
    </div>
    <div class="manager-panels">
      <form id="requestForm" class="surface-card stack">
        <label><span>Titre</span><input name="titre" required /></label>
        <label><span>Auteur</span><input name="auteur" /></label>
        <label><span>ISBN</span><input name="isbn" /></label>
        <label><span>Catégorie suggérée</span><input name="categorie_suggeree" /></label>
        <label><span>Description du besoin</span><textarea name="description"></textarea></label>
        <button class="btn btn-primary" type="submit">Demander</button>
      </form>
      <div>
        <div class="surface-card">
          <h3>Mes demandes</h3>
          <div id="requestList" class="requests-grid"></div>
        </div>
      </div>
    </div>
  `;

  const renderRequests = (requests) => {
    const normalized = Array.isArray(requests) ? requests.map(normalizeRequest) : [];
    document.getElementById("requestList").innerHTML =
      normalized.map((request) => requestReaderCard(request)).join("") ||
      emptyState("Aucune requête pour le moment.");
    return normalized;
  };

  let currentRequests = [];

  const loadRequests = async () => {
    const requests = await apiFetch(`${API.livres}/demandes-livres/`);
    currentRequests = renderRequests(requests);
  };

  document.getElementById("requestForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());

    try {
      const recherche = await apiFetch(
        `${API.livres}/livres/recherche/?q=${encodeURIComponent(data.isbn || data.titre || "")}`
      );
      const livresTrouves = Array.isArray(recherche) ? recherche : [];
      const existe = livresTrouves.some((livre) => {
        const memeIsbn = data.isbn && String(livre.isbn || "").toLowerCase() === data.isbn.toLowerCase();
        const memeTitre = String(livre.titre || "").toLowerCase() === data.titre.toLowerCase();
        return memeIsbn || memeTitre;
      });

      if (existe) {
        showToast("Ce livre est déjà disponible.");
        return;
      }

      const createdRequest = await apiFetch(`${API.livres}/demandes-livres/`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      form.reset();
      currentRequests = [normalizeRequest(createdRequest), ...currentRequests];
      renderRequests(currentRequests);
      showToast("Requête envoyée.");
    } catch (error) {
      handleError(error);
    }
  });

  await loadRequests();
}

async function renderManagerBooksTab(panel) {
  const livres = await apiFetch(`${API.livres}/livres/?limite=300`);
  panel.innerHTML = `
    <div class="panel-header">
      <div>
        <p class="eyebrow">Gestion</p>
        <h2>Gestion de livres</h2>
        <p>Liste complète, recherche, ajout, modification et suppression du catalogue.</p>
      </div>
      <button id="resetBookForm" class="btn btn-secondary" type="button">Nouveau livre</button>
    </div>
    <div class="stack">
      <form id="managerBookForm" class="surface-card stack">
        <div>
          <p class="eyebrow">Ajout / modification</p>
          <h3>Ajouter un nouveau livre</h3>
        </div>
        <input name="id" type="hidden" />
        <label><span>Titre</span><input name="titre" required /></label>
        <label><span>Auteur</span><input name="auteur" required /></label>
        <label><span>ISBN</span><input name="isbn" required /></label>
        <label><span>Catégorie</span><input name="categorie" required /></label>
        <label><span>Description</span><textarea name="description"></textarea></label>
        <label><span>Langue</span><input name="langue" value="Français" /></label>
        <label><span>URL image</span><input name="image_url" /></label>
        <label><span>Quantité totale</span><input name="quantite_totale" type="number" min="1" value="1" required /></label>
        <label><span>Quantité disponible</span><input name="quantite_disponible" type="number" min="0" value="1" required /></label>
        <div class="form-actions">
          <button class="btn btn-primary" type="submit">Enregistrer</button>
        </div>
      </form>
      <div class="surface-card">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Catalogue</p>
            <h3>Liste des livres</h3>
          </div>
        </div>
        <div class="split-actions">
          <input id="managerBookSearch" placeholder="Rechercher un livre..." />
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Titre</th>
                <th>Auteur</th>
                <th>Catégorie</th>
                <th>Stock</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="managerBookRows"></tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  const rows = document.getElementById("managerBookRows");
  const form = document.getElementById("managerBookForm");
  const searchInput = document.getElementById("managerBookSearch");

  const renderRows = () => {
    const query = searchInput.value.trim().toLowerCase();
    const filtered = livres.filter((livre) =>
      [livre.titre, livre.auteur, livre.categorie, livre.isbn]
        .some((value) => String(value || "").toLowerCase().includes(query))
    );

    rows.innerHTML = filtered
      .map(
        (livre) => `
          <tr>
            <td>${escapeHtml(livre.titre)}</td>
            <td>${escapeHtml(livre.auteur)}</td>
            <td>${escapeHtml(livre.categorie)}</td>
            <td>${livre.quantite_disponible}/${livre.quantite_totale}</td>
            <td>
              <div class="table-actions">
                <button type="button" class="btn btn-secondary" data-edit-book="${livre.id}">Modifier</button>
                <button type="button" class="btn btn-danger" data-delete-book="${livre.id}">Supprimer</button>
              </div>
            </td>
          </tr>
        `
      )
      .join("");
  };

  searchInput.addEventListener("input", renderRows);
  document.getElementById("resetBookForm").addEventListener("click", () => {
    form.reset();
    form.elements.namedItem("langue").value = "Français";
    form.elements.namedItem("quantite_totale").value = "1";
    form.elements.namedItem("quantite_disponible").value = "1";
  });

  rows.addEventListener("click", async (event) => {
    const editButton = event.target.closest("[data-edit-book]");
    const deleteButton = event.target.closest("[data-delete-book]");

    if (editButton) {
      const livre = livres.find((item) => item.id === Number(editButton.dataset.editBook));
      fillForm(form, livre);
      return;
    }

    if (deleteButton) {
      const livre = livres.find((item) => item.id === Number(deleteButton.dataset.deleteBook));
      if (!window.confirm(`Êtes vous sur que vous voulez supprimer le livre ${livre.titre} ?`)) {
        return;
      }
      try {
        await apiFetch(`${API.livres}/livres/${livre.id}/`, { method: "DELETE" });
        showToast("Livre supprimé.");
        await renderManagerBooksTab(panel);
      } catch (error) {
        handleError(error);
      }
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    data.quantite_totale = Number(data.quantite_totale);
    data.quantite_disponible = Number(data.quantite_disponible);
    const bookId = data.id;
    delete data.id;

    try {
      if (bookId) {
        await apiFetch(`${API.livres}/livres/${bookId}/`, {
          method: "PATCH",
          body: JSON.stringify(data),
        });
        showToast("Livre modifié.");
      } else {
        await apiFetch(`${API.livres}/livres/`, {
          method: "POST",
          body: JSON.stringify(data),
        });
        showToast("Livre ajouté.");
      }
      await renderManagerBooksTab(panel);
    } catch (error) {
      handleError(error);
    }
  });

  renderRows();
}

async function renderManagerRequestsTab(panel) {
  const requests = await apiFetch(`${API.livres}/demandes-livres/`);
  panel.innerHTML = `
    <div class="panel-header">
      <div>
        <p class="eyebrow">Flux de demandes</p>
        <h2>Gestion requêtes</h2>
        <p>Consultez les demandes, mettez à jour leur statut et clôturez les dossiers.</p>
      </div>
    </div>
    <div id="managerRequestsGrid" class="requests-grid">
      ${
        requests.map((request) => requestManagerCard(request)).join("") ||
        emptyState("Aucune requête à traiter.")
      }
    </div>
  `;

  document.getElementById("managerRequestsGrid").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-save-request]");
    if (!button) {
      return;
    }

    const requestId = Number(button.dataset.saveRequest);
    const card = button.closest("[data-request-card]");
    const statut = card.querySelector("select").value;
    const commentaire = card.querySelector("textarea").value;

    try {
      await apiFetch(`${API.livres}/demandes-livres/${requestId}/`, {
        method: "PATCH",
        body: JSON.stringify({
          statut,
          commentaire_gestionnaire: commentaire,
        }),
      });
      showToast("Statut mis à jour.");
      await renderManagerRequestsTab(panel);
    } catch (error) {
      handleError(error);
    }
  });
}

async function renderAdminStatsTab(panel) {
  const [dashboard, top, repartition, sante] = await Promise.all([
    apiFetch(`${API.statistiques}/statistiques/tableau-de-bord/`),
    apiFetch(`${API.statistiques}/statistiques/top-livres/`),
    apiFetch(`${API.statistiques}/statistiques/repartition-utilisateurs/`),
    apiFetch(`${API.statistiques}/statistiques/sante-services/`),
  ]);

  panel.innerHTML = `
    <div class="panel-header">
      <div>
        <p class="eyebrow">Pilotage</p>
        <h2>Stats de la plateforme</h2>
        <p>Vue globale de l'activité, de l'usage du fonds et de l'état des services.</p>
      </div>
    </div>
    <div class="stat-grid">
      ${Object.entries(dashboard)
        .filter(([key]) => key !== "erreurs")
        .map(
          ([key, value]) => `
            <article class="stat-card">
              <span>${escapeHtml(humanizeKey(key))}</span>
              <strong>${escapeHtml(String(value))}</strong>
            </article>
          `
        )
        .join("")}
    </div>
    <div class="stats-layout">
      <div class="surface-card">
        <h3>Top livres empruntés</h3>
        <div class="stack">
          ${barList(top, "livre", "total")}
        </div>
      </div>
      <div class="surface-card">
        <h3>Répartition des rôles</h3>
        <div class="chart-box"><canvas id="adminRoleChart" width="280" height="280"></canvas></div>
      </div>
    </div>
    <div class="surface-card">
      <h3>Santé des services</h3>
      <div class="requests-grid">
        ${Object.entries(sante)
          .map(
            ([service, state]) => `
              <article class="request-card">
                <strong>${escapeHtml(service)}</strong>
                <span class="status-pill ${state === "ok" ? "status-available" : "status-warning"}">${escapeHtml(state)}</span>
              </article>
            `
          )
          .join("")}
      </div>
    </div>
  `;

  drawPieChart(
    document.getElementById("adminRoleChart"),
    repartition.reduce((acc, item) => {
      acc[roleLabel(item.type_utilisateur)] = item.total;
      return acc;
    }, {})
  );
}

async function renderAdminToolsTab(panel) {
  panel.innerHTML = `
    <div class="panel-header">
      <div>
        <p class="eyebrow">Back-office</p>
        <h2>Administration Django</h2>
        <p>Accédez aux écrans CRUD des microservices pour gérer utilisateurs, livres, requêtes et emprunts.</p>
      </div>
    </div>
    <div class="admin-links">
      ${ADMIN_LINKS.map(adminLinkCard).join("")}
    </div>
  `;
}

function renderBookCollection(container, livres, options = {}) {
  container.innerHTML =
    livres.map((livre) => bookCard(livre, options)).join("") || emptyState("Aucun livre à afficher.");
}

function bookCard(livre, options = {}) {
  return `
    <article class="book-card">
      <div class="book-cover"><span>${escapeHtml(initials(livre.titre || "Livre"))}</span></div>
      <div class="book-card-body">
        <div class="status-row">
          <span class="tag">${escapeHtml(livre.categorie || "Catalogue")}</span>
          <span class="status-pill ${livre.quantite_disponible > 0 ? "status-available" : "status-unavailable"}">
            ${escapeHtml(livre.disponibilite || (livre.quantite_disponible > 0 ? "Disponible" : "Pas disponible"))}
          </span>
        </div>
        <h3>${escapeHtml(livre.titre || "Titre indisponible")}</h3>
        <div class="book-meta">
          <span>Auteur : ${escapeHtml(livre.auteur || "Non renseigné")}</span>
          <span>ISBN : ${escapeHtml(livre.isbn || "-")}</span>
          <span>Stock : ${livre.quantite_disponible ?? 0}/${livre.quantite_totale ?? 0}</span>
          ${
            options.showScore && livre.recommendationScore !== undefined
              ? `<span>Score recommandation : ${escapeHtml(String(livre.recommendationScore))}</span>`
              : ""
          }
          <span>${escapeHtml(livre.description || "Description non renseignée.")}</span>
        </div>
      </div>
    </article>
  `;
}

function borrowCard(livre) {
  const disponible = livre.quantite_disponible > 0;
  return `
    <article class="book-card">
      <div class="book-cover"><span>${escapeHtml(initials(livre.titre))}</span></div>
      <div class="book-card-body">
        <div class="status-row">
          <span class="tag">${escapeHtml(livre.categorie || "Catalogue")}</span>
          <span class="status-pill ${disponible ? "status-available" : "status-unavailable"}">
            ${disponible ? "Disponible" : "Pas disponible"}
          </span>
        </div>
        <h3>${escapeHtml(livre.titre)}</h3>
        <p class="book-meta">Auteur : ${escapeHtml(livre.auteur)}</p>
        <p class="book-meta">${escapeHtml(livre.description || "Description non renseignée.")}</p>
        <button class="btn ${disponible ? "btn-primary" : "btn-secondary"}" type="button" data-borrow-id="${livre.id}" ${
          disponible ? "" : "disabled"
        }>
          Emprunter
        </button>
      </div>
    </article>
  `;
}

function requestReaderCard(request) {
  return `
    <article class="request-card">
      <div class="status-row">
        <strong>${escapeHtml(request.titre)}</strong>
        <span class="status-pill ${requestStatusClass(request.statut)}">${escapeHtml(request.statut_label)}</span>
      </div>
      <span>Auteur : ${escapeHtml(request.auteur || "Non renseigné")}</span>
      <span>ISBN : ${escapeHtml(request.isbn || "-")}</span>
      <span>${escapeHtml(request.description || "Aucune précision fournie.")}</span>
      ${
        request.commentaire_gestionnaire
          ? `<span class="muted">Commentaire gestionnaire : ${escapeHtml(request.commentaire_gestionnaire)}</span>`
          : ""
      }
    </article>
  `;
}

function normalizeRequest(request) {
  const statusLabels = {
    en_cours_traitement: "En cours de traitement",
    en_attente_livre: "En attente du livre",
    refuse: "Refusé",
    livre_disponible: "Livre disponible",
    cloturee: "Clôturée",
  };

  return {
    ...request,
    titre: request?.titre || "Titre non renseigné",
    auteur: request?.auteur || "",
    isbn: request?.isbn || "",
    description: request?.description || "",
    commentaire_gestionnaire: request?.commentaire_gestionnaire || "",
    statut: request?.statut || "en_cours_traitement",
    statut_label: request?.statut_label || statusLabels[request?.statut] || "En cours de traitement",
  };
}

function requestManagerCard(request) {
  return `
    <article class="request-card" data-request-card>
      <div class="status-row">
        <strong>${escapeHtml(request.titre)}</strong>
        <span class="status-pill ${requestStatusClass(request.statut)}">${escapeHtml(request.statut_label)}</span>
      </div>
      <span>Demandeur : ${escapeHtml(request.utilisateur_nom)}</span>
      <span>Auteur : ${escapeHtml(request.auteur || "Non renseigné")}</span>
      <span>Description : ${escapeHtml(request.description || "Aucune description")}</span>
      <label>
        <span>Statut</span>
        <select>
          ${requestStatusOptions(request.statut)}
        </select>
      </label>
      <label>
        <span>Commentaire</span>
        <textarea>${escapeHtml(request.commentaire_gestionnaire || "")}</textarea>
      </label>
      <button class="btn btn-primary" type="button" data-save-request="${request.id}">Enregistrer</button>
    </article>
  `;
}

function requestStatusOptions(current) {
  const statuses = [
    ["en_cours_traitement", "En cours de traitement"],
    ["en_attente_livre", "En attente du livre"],
    ["refuse", "Refusé"],
    ["livre_disponible", "Livre disponible"],
    ["cloturee", "Clôturée"],
  ];

  return statuses
    .map(
      ([value, label]) =>
        `<option value="${value}" ${current === value ? "selected" : ""}>${escapeHtml(label)}</option>`
    )
    .join("");
}

function adminLinkCard(link) {
  return `
    <article class="admin-link-card">
      <span class="eyebrow">CRUD</span>
      <h3>${escapeHtml(link.label)}</h3>
      <p>${escapeHtml(link.text)}</p>
      <a class="btn btn-primary" href="${link.href}" target="_blank" rel="noreferrer">Ouvrir</a>
    </article>
  `;
}

function drawPieChart(canvas, data) {
  if (!canvas) {
    return;
  }
  const ctx = canvas.getContext("2d");
  const entries = Object.entries(data).filter(([, value]) => value > 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!entries.length) {
    ctx.fillStyle = "#6d8890";
    ctx.font = "16px Trebuchet MS";
    ctx.textAlign = "center";
    ctx.fillText("Aucune donnée", canvas.width / 2, canvas.height / 2);
    return;
  }

  const total = entries.reduce((sum, [, value]) => sum + value, 0);
  let angle = -Math.PI / 2;
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const radius = Math.min(centerX, centerY) - 16;

  entries.forEach(([label, value], index) => {
    const slice = (value / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.arc(centerX, centerY, radius, angle, angle + slice);
    ctx.closePath();
    ctx.fillStyle = PIE_COLORS[index % PIE_COLORS.length];
    ctx.fill();
    angle += slice;
  });

  ctx.beginPath();
  ctx.fillStyle = "#ffffff";
  ctx.arc(centerX, centerY, radius * 0.58, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#1b5a68";
  ctx.font = "700 18px Trebuchet MS";
  ctx.textAlign = "center";
  ctx.fillText(String(total), centerX, centerY - 4);
  ctx.font = "14px Trebuchet MS";
  ctx.fillText("emprunts", centerX, centerY + 18);
}

function barList(items, labelKey, valueKey) {
  if (!items.length) {
    return "<p class='muted'>Aucune donnée.</p>";
  }
  const max = Math.max(...items.map((item) => item[valueKey]), 1);
  return items
    .map(
      (item) => `
        <div class="stack">
          <div class="status-row">
            <strong>${escapeHtml(item[labelKey])}</strong>
            <span>${item[valueKey]}</span>
          </div>
          <div style="height:10px;border-radius:999px;background:rgba(27,90,104,0.08);overflow:hidden;">
            <div style="height:100%;width:${(item[valueKey] / max) * 100}%;background:linear-gradient(90deg,#1b5a68,#6d8890);"></div>
          </div>
        </div>
      `
    )
    .join("");
}

function fillForm(form, data) {
  Object.entries(data).forEach(([key, value]) => {
    const field = form.elements.namedItem(key);
    if (field) {
      field.value = value ?? "";
    }
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value);
}

function initials(text) {
  return String(text)
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

function roleLabel(role) {
  const labels = {
    etudiant: "Étudiant",
    professeur: "Professeur",
    gestionnaire: "Gestionnaire",
    admin: "Administrateur",
  };
  return labels[role] || role;
}

function roleDescription(role) {
  const descriptions = {
    etudiant: "Consultation du catalogue, emprunts, historique, stats personnelles et demandes de livres.",
    professeur: "Consultation du catalogue, emprunts, historique, stats personnelles et demandes de livres.",
    gestionnaire: "Mise à jour du fonds documentaire et traitement opérationnel des demandes.",
    admin: "Pilotage global de la plateforme et accès au back-office Django.",
  };
  return descriptions[role] || "";
}

function requestStatusClass(status) {
  if (status === "refuse") {
    return "status-unavailable";
  }
  if (status === "livre_disponible") {
    return "status-available";
  }
  return "status-warning";
}

function labelForLoanStatus(status) {
  const labels = {
    en_cours: "En cours",
    retourne: "Retourné",
    en_retard: "En retard",
  };
  return labels[status] || status;
}

function statusClassForLoan(status) {
  if (status === "retourne") {
    return "status-available";
  }
  if (status === "en_retard") {
    return "status-unavailable";
  }
  return "status-warning";
}

function emptyState(message) {
  return `<div class="empty-state"><p>${escapeHtml(message)}</p></div>`;
}

function loadingState(message) {
  return `<div class="empty-state"><p>${escapeHtml(message)}</p></div>`;
}

function humanizeKey(key) {
  return key.replaceAll("_", " ");
}

function formatDate(value) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(new Date(value));
}

function futureDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function formatErrorText(text) {
  const trimmed = String(text || "").trim();
  if (!trimmed) {
    return "Erreur serveur";
  }

  if (trimmed.startsWith("<!DOCTYPE html") || trimmed.startsWith("<html")) {
    const titleMatch = trimmed.match(/<title>(.*?)<\/title>/i);
    if (titleMatch?.[1]) {
      return `Erreur serveur: ${titleMatch[1]}`;
    }
    return "Erreur serveur";
  }

  return trimmed;
}

function debounce(fn, delay) {
  let timeoutId = null;
  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => fn(...args), delay);
  };
}
