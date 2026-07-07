const parseEuro = (value) => {
    const normalized = String(value || "0").replace(",", ".").replace(/[^\d.-]/g, "");
    const parsed = Number.parseFloat(normalized);
    return Number.isFinite(parsed) ? parsed : 0;
};

const formatEuro = (value) => `${value.toFixed(2)} EUR`;

document.querySelectorAll("[data-budget-form]").forEach((form) => {
    const price = form.querySelector("[data-price]");
    const paid = form.querySelector("[data-paid]");
    const vat = form.querySelector("[data-vat]");
    const preview = form.querySelector("[data-budget-preview]");

    const updatePreview = () => {
        const base = parseEuro(price.value);
        const iva = vat.checked ? base * 0.23 : 0;
        const total = base + iva;
        const open = Math.max(0, total - parseEuro(paid.value));
        preview.innerHTML = `
            <span>IVA: ${formatEuro(iva)}</span>
            <strong>Total: ${formatEuro(total)}</strong>
            <small>Em aberto: ${formatEuro(open)}</small>
        `;
    };

    ["input", "change"].forEach((eventName) => {
        form.addEventListener(eventName, updatePreview);
    });
    updatePreview();
});

document.querySelectorAll("[data-autosubmit]").forEach((form) => {
    const field = form.querySelector("input[name='q']");
    if (!field) {
        return;
    }
    let timer;
    field.addEventListener("input", () => {
        window.clearTimeout(timer);
        timer = window.setTimeout(() => {
            form.requestSubmit();
        }, 520);
    });
});

document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        document.querySelector("[data-global-search]")?.focus();
    }
});

document.querySelectorAll("[data-open-dialog]").forEach((button) => {
    const dialog = document.getElementById(button.dataset.openDialog);
    button.addEventListener("click", () => {
        if (!dialog) {
            return;
        }
        if (typeof dialog.showModal === "function") {
            dialog.showModal();
        } else {
            dialog.setAttribute("open", "");
        }
        dialog.querySelector("[data-dialog-focus]")?.focus();
    });
});

document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => {
        const dialog = button.closest("dialog");
        if (dialog && typeof dialog.close === "function") {
            dialog.close();
        } else {
            dialog?.removeAttribute("open");
        }
    });
});

if (window.location.hash === "#add-product") {
    document.querySelector('[data-open-dialog="product-dialog"]')?.click();
}

document.querySelectorAll("[data-material-consumption]").forEach((section) => {
    const rows = section.querySelector("[data-material-rows]");
    const addButton = section.querySelector("[data-add-material]");

    const refreshRow = (row) => {
        const select = row.querySelector("[data-material-select]");
        const qty = row.querySelector("[data-material-qty]");
        const hint = row.querySelector("[data-material-hint]");
        const selected = select.options[select.selectedIndex];
        const stock = selected?.dataset.stock;
        if (!stock) {
            hint.textContent = "";
            qty.removeAttribute("max");
            return;
        }
        qty.max = stock;
        hint.textContent = `Disponivel em stock: ${stock}`;
    };

    const setupRow = (row) => {
        row.querySelector("[data-material-select]")?.addEventListener("change", () => refreshRow(row));
        row.querySelector("[data-remove-material]")?.addEventListener("click", () => {
            if (rows.querySelectorAll("[data-material-row]").length === 1) {
                row.querySelector("[data-material-select]").value = "";
                row.querySelector("[data-material-qty]").value = "1";
                refreshRow(row);
                return;
            }
            row.remove();
        });
        refreshRow(row);
    };

    rows.querySelectorAll("[data-material-row]").forEach(setupRow);

    addButton?.addEventListener("click", () => {
        const source = rows.querySelector("[data-material-row]");
        const clone = source.cloneNode(true);
        clone.querySelector("[data-material-select]").value = "";
        clone.querySelector("[data-material-qty]").value = "1";
        clone.querySelector("[data-material-hint]").textContent = "";
        rows.appendChild(clone);
        setupRow(clone);
    });
});

// Clickable table rows: navigate to `data-href` on click, but ignore clicks on interactive elements
document.addEventListener("click", (e) => {
    const row = e.target.closest("tr[data-href]");
    if (!row) return;
    if (e.target.closest("a, button, form, input, select, textarea")) return;
    const href = row.getAttribute("data-href");
    if (href) {
        window.location.href = href;
    }
});

// Character counter for observações textarea
document.querySelectorAll("[data-obs-counter]").forEach((textarea) => {
    const counter = textarea.closest("label")?.querySelector("[data-char-counter]");
    if (!counter) return;
    const max = parseInt(textarea.getAttribute("maxlength"), 10) || 500;

    const update = () => {
        const remaining = max - textarea.value.length;
        counter.textContent = `${remaining} caracteres restantes`;
        counter.classList.toggle("limit", remaining < 50);
    };

    textarea.addEventListener("input", update);
    update();
});
