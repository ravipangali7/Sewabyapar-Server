(function () {
  const root = document.getElementById("travelApp");
  if (!root) return;

  const role = root.dataset.role;
  const apiBase = root.dataset.apiBase || "/api/travel";
  const coreApiBase = "/api";
  const state = { session: null, tab: "dashboard", data: {}, query: "", pageData: [] };

  const el = {
    alert: document.getElementById("appAlert"),
    tabList: document.getElementById("tabList"),
    desktopMenu: document.getElementById("desktopMenu"),
    mobileMenu: document.getElementById("mobileMenu"),
    kpiGrid: document.getElementById("kpiGrid"),
    panelTitle: document.getElementById("panelTitle"),
    panelActions: document.getElementById("panelActions"),
    panelBody: document.getElementById("panelBody"),
    refreshBtn: document.getElementById("refreshBtn"),
    searchInput: document.getElementById("searchInput"),
    modalRoot: document.getElementById("modalRoot"),
    modalTitle: document.getElementById("modalTitle"),
    modalForm: document.getElementById("modalForm"),
    modalClose: document.getElementById("modalClose"),
  };

  const roleConfig = {
    travel_committee: ["dashboard", "vehicles", "bookings", "boarding", "staff", "revenue", "wallet"],
    travel_staff: ["dashboard", "bookings", "boarding", "revenue"],
    travel_dealer: ["dashboard", "bookings", "agents", "revenue", "wallet"],
    agent: ["dashboard", "bookings", "create-booking", "vehicles", "revenue", "wallet"],
  };

  function csrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  async function api(path, options = {}) {
    const res = await fetch(path, {
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
        ...(options.headers || {}),
      },
      ...options,
    });
    const isJson = (res.headers.get("content-type") || "").includes("application/json");
    const data = isJson ? await res.json() : null;
    if (!res.ok) throw new Error((data && (data.error || data.detail)) || `Request failed (${res.status})`);
    return data;
  }

  function showAlert(message, type) {
    el.alert.className = "mb-3 rounded-lg px-3 py-2 text-sm";
    const map = {
      success: "bg-green-100 text-green-700 border border-green-300",
      error: "bg-red-100 text-red-700 border border-red-300",
      warning: "bg-yellow-100 text-yellow-700 border border-yellow-300",
    };
    el.alert.classList.add(...(map[type] || map.warning).split(" "));
    el.alert.textContent = message;
    el.alert.classList.remove("hidden");
  }

  function clearAlert() {
    el.alert.classList.add("hidden");
  }

  function fieldHtml(field) {
    const required = field.required ? "required" : "";
    const disabled = field.disabled ? "disabled" : "";
    const value = field.value || "";
    if (field.type === "textarea") {
      return `<textarea name="${field.name}" class="w-full border border-gray-300 rounded-lg px-3 py-2" ${required} ${disabled}>${value}</textarea>`;
    }
    if (field.type === "select") {
      return `<select name="${field.name}" class="w-full border border-gray-300 rounded-lg px-3 py-2" ${required} ${disabled}>
        ${(field.options || [])
          .map((opt) => `<option value="${opt.value}" ${String(opt.value) === String(value) ? "selected" : ""}>${opt.label}</option>`)
          .join("")}
      </select>`;
    }
    return `<input name="${field.name}" type="${field.type || "text"}" value="${value}" class="w-full border border-gray-300 rounded-lg px-3 py-2" ${required} ${disabled} />`;
  }

  function parseApiErrorMessage(err) {
    if (!err) return "Request failed";
    const message = String(err.message || err);
    if (!message.startsWith("{")) return message;
    try {
      const parsed = JSON.parse(message);
      if (parsed.error) return String(parsed.error);
      if (parsed.detail) return String(parsed.detail);
      const firstKey = Object.keys(parsed)[0];
      if (!firstKey) return "Request failed";
      const firstVal = parsed[firstKey];
      if (Array.isArray(firstVal)) return `${firstKey}: ${firstVal[0]}`;
      if (typeof firstVal === "string") return `${firstKey}: ${firstVal}`;
      return `${firstKey}: ${JSON.stringify(firstVal)}`;
    } catch (_) {
      return message;
    }
  }

  function openModal(title, fields, onSubmit, submitLabel = "Save", modalOptions) {
    const opts = modalOptions || {};
    el.modalTitle.textContent = title;
    el.modalForm.innerHTML = "";
    fields.forEach((field) => {
      const wrap = document.createElement("div");
      const help = field.helpText ? `<p class="text-xs text-gray-500 mt-1">${field.helpText}</p>` : "";
      wrap.innerHTML = `<label class="block text-sm text-gray-700 mb-1">${field.label}</label>${fieldHtml(field)}${help}`;
      el.modalForm.appendChild(wrap);
    });
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.className = "bg-red-600 text-white px-4 py-2 rounded-lg";
    submit.textContent = submitLabel;
    el.modalForm.appendChild(submit);
    el.modalForm.onsubmit = async (e) => {
      e.preventDefault();
      const formData = new FormData(el.modalForm);
      const payload = {};
      for (const [k, v] of formData.entries()) payload[k] = v;
      try {
        await onSubmit(payload);
        closeModal();
        if (!opts.silentSuccess) {
          showAlert("Saved successfully", "success");
          refreshCurrent();
        }
      } catch (err) {
        showAlert(parseApiErrorMessage(err), "error");
      }
    };
    el.modalRoot.classList.remove("hidden");
    el.modalRoot.classList.add("flex");
  }

  function closeModal() {
    el.modalRoot.classList.add("hidden");
    el.modalRoot.classList.remove("flex");
  }

  function tabsForRole() {
    const all = roleConfig[role] || ["dashboard"];
    if (role === "travel_staff" && state.session && state.session.staff) {
      return all.filter((tab) => {
        if (tab === "bookings") return state.session.staff.booking_permission;
        if (tab === "boarding") return state.session.staff.boarding_permission;
        if (tab === "revenue") return state.session.staff.finance_permission;
        return true;
      });
    }
    return all;
  }

  function drawMenu() {
    const tabs = tabsForRole();
    const makeBtn = (key) =>
      `<button data-tab="${key}" class="travel-tab drawer-item w-full text-left px-3 py-2 rounded-lg ${
        state.tab === key ? "active" : "text-gray-700"
      }">${key.replace("-", " ").toUpperCase()}</button>`;
    el.tabList.innerHTML = tabs.map((t) => makeBtn(t)).join("");
    el.desktopMenu.innerHTML = tabs.map((t) => makeBtn(t)).join("");
    el.mobileMenu.innerHTML = tabs
      .slice(0, 4)
      .map(
        (t) =>
          `<button data-tab="${t}" class="travel-tab px-2 py-3 ${
            state.tab === t ? "text-red-600 font-semibold" : "text-gray-600"
          }">${t.split("-")[0]}</button>`
      )
      .join("");
    root.querySelectorAll("[data-tab]").forEach((btn) =>
      btn.addEventListener("click", () => {
        state.tab = btn.dataset.tab;
        render();
      })
    );
  }

  function renderStats(obj) {
    const entries = Object.entries(obj || {}).slice(0, 8);
    el.kpiGrid.innerHTML = entries
      .map(
        ([k, v]) =>
          `<div class="travel-stat p-3"><div class="text-xs text-gray-500">${k.replace(/_/g, " ")}</div><div class="text-lg font-bold text-gray-900">${
            typeof v === "object" ? JSON.stringify(v) : v
          }</div></div>`
      )
      .join("");
  }

  function tableFromArray(items, columns, rowActions) {
    if (!items || !items.length) return `<div class="text-sm text-gray-500">No data found.</div>`;
    const keys = columns || Object.keys(items[0]).slice(0, 8);
    const head = `<tr>${keys.map((k) => `<th class="text-left p-2 border-b">${labelize(k)}</th>`).join("")}${
      rowActions ? `<th class="text-left p-2 border-b">Actions</th>` : ""
    }</tr>`;
    const rows = items
      .map((item, index) => {
        const cells = keys.map((k) => `<td class="p-2 border-b text-sm">${normalize(resolve(item, k))}</td>`).join("");
        const actions = rowActions
          ? `<td class="p-2 border-b text-sm">${rowActions
              .map((a) => `<button data-row="${index}" data-act="${a.id}" class="mr-1 mb-1 text-xs px-2 py-1 rounded ${a.className || "bg-gray-100"}">${a.label}</button>`)
              .join("")}</td>`
          : "";
        return `<tr>${cells}${actions}</tr>`;
      })
      .join("");
    return `<table class="w-full min-w-[720px]">${head}${rows}</table>`;
  }

  function resolve(obj, path) {
    return path.split(".").reduce((acc, key) => (acc ? acc[key] : undefined), obj);
  }

  function labelize(k) {
    return k.replace(/\./g, " ").replace(/_/g, " ");
  }

  function normalize(v) {
    if (v === null || v === undefined) return "-";
    if (typeof v === "object") return JSON.stringify(v).slice(0, 120);
    return String(v);
  }

  function actionButton(label, handler, cls) {
    const btn = document.createElement("button");
    btn.className = cls || "bg-red-600 text-white px-3 py-2 rounded-lg text-sm";
    btn.textContent = label;
    btn.onclick = handler;
    el.panelActions.appendChild(btn);
  }

  async function loadDashboard() {
    const map = {
      travel_committee: `${apiBase}/dashboard/committee/`,
      travel_staff: `${apiBase}/dashboard/staff/`,
      travel_dealer: `${apiBase}/dashboard/dealer/`,
      agent: `${apiBase}/dashboard/agent/`,
    };
    const data = await api(map[role]);
    state.data.dashboard = data;
    renderStats(data.stats || data.widgets || {});
    const profile = data.committee || data.staff || data.dealer || data.agent || {};
    el.panelBody.innerHTML = `<div class="grid md:grid-cols-2 gap-3">
      <div class="travel-card p-3"><div class="text-xs text-gray-500 mb-2">Role Summary</div><pre class="text-xs whitespace-pre-wrap">${JSON.stringify(profile, null, 2)}</pre></div>
      <div class="travel-card p-3"><div class="text-xs text-gray-500 mb-2">Response Snapshot</div><pre class="text-xs whitespace-pre-wrap">${JSON.stringify(data, null, 2).slice(0, 2000)}</pre></div>
    </div>`;
  }

  async function loadBookings() {
    const data = await api(`${apiBase}/bookings/`);
    state.data.bookings = data;
    state.pageData = data.filter(filterBySearch);
    renderStats({});
    el.panelBody.innerHTML = tableFromArray(
      state.pageData,
      ["id", "ticket_number", "name", "phone", "status", "booking_date", "booking_revenue", "fare"],
      [
        { id: "view", label: "View", className: "bg-blue-50" },
        ...(role === "travel_committee" || role === "travel_staff"
          ? [{ id: "edit", label: "Edit", className: "bg-yellow-50" }]
          : []),
        { id: "ticket", label: "Ticket", className: "bg-green-50" },
      ]
    );
    actionButton("Refresh Bookings", refreshCurrent);
    if (role === "agent" || (role === "travel_staff" && state.session?.staff?.booking_permission)) {
      actionButton("Create Booking", createBookingFlow);
    }
    bindRowActions({
      view: async (row) => showAlert(`Booking ${row.ticket_number || row.id}`, "success"),
      edit: async (row) =>
        openModal(
          "Update Booking",
          [
            { name: "name", label: "Name", value: row.name, required: true },
            { name: "phone", label: "Phone", value: row.phone, required: true },
            {
              name: "status",
              label: "Status",
              type: "select",
              value: row.status,
              options: ["pending", "booked", "boarded", "cancelled"].map((s) => ({ value: s, label: s })),
            },
            { name: "remarks", label: "Remarks", type: "textarea", value: row.remarks || "" },
          ],
          (payload) => api(`${apiBase}/bookings/${row.id}/`, { method: "PATCH", body: JSON.stringify(payload) }),
          "Update"
        ),
      ticket: async (row) => window.open(`${apiBase}/bookings/${row.id}/ticket/`, "_blank"),
    });
  }

  async function loadVehicles() {
    const data = await api(`${apiBase}/vehicles/`);
    state.data.vehicles = data;
    state.pageData = data.filter(filterBySearch);
    el.panelBody.innerHTML = tableFromArray(
      state.pageData,
      ["id", "name", "vehicle_no", "from_place.name", "to_place.name", "departure_time", "is_active", "seat_price"],
      role === "travel_committee"
        ? [
            { id: "edit", label: "Edit", className: "bg-yellow-50" },
            { id: "delete", label: "Delete", className: "bg-red-50" },
          ]
        : null
    );
    if (role === "travel_committee") {
      actionButton("Add Vehicle", () =>
        openModal(
          "Create Vehicle",
          [
            { name: "name", label: "Name", required: true },
            { name: "vehicle_no", label: "Vehicle No", required: true },
            { name: "from_place", label: "From Place ID", required: true },
            { name: "to_place", label: "To Place ID", required: true },
            { name: "departure_time", label: "Departure Time (HH:MM)", required: true },
            { name: "actual_seat_price", label: "Actual Seat Price", required: true },
            { name: "seat_price", label: "Seat Price", required: true },
          ],
          (payload) => api(`${apiBase}/vehicles/`, { method: "POST", body: JSON.stringify(payload) })
        )
      );
      bindRowActions({
        edit: async (row) =>
          openModal(
            "Update Vehicle",
            [
              { name: "name", label: "Name", value: row.name, required: true },
              { name: "vehicle_no", label: "Vehicle No", value: row.vehicle_no, required: true },
              { name: "departure_time", label: "Departure Time", value: row.departure_time, required: true },
              { name: "actual_seat_price", label: "Actual Seat Price", value: row.actual_seat_price, required: true },
              { name: "seat_price", label: "Seat Price", value: row.seat_price, required: true },
            ],
            (payload) => api(`${apiBase}/vehicles/${row.id}/`, { method: "PATCH", body: JSON.stringify(payload) }),
            "Update"
          ),
        delete: async (row) => {
          if (!window.confirm(`Delete or deactivate ${row.name}?`)) return;
          await api(`${apiBase}/vehicles/${row.id}/`, { method: "DELETE" });
          showAlert("Vehicle delete/deactivate completed", "success");
          await refreshCurrent();
        },
      });
    }
  }

  async function loadBoarding() {
    const data = await api(`${apiBase}/boarding/`);
    state.data.boarding = data;
    state.pageData = data.filter(filterBySearch);
    el.panelBody.innerHTML = tableFromArray(state.pageData, ["id", "ticket_number", "name", "phone", "status", "booking_date"], [
      { id: "confirm", label: "Confirm Boarding", className: "bg-green-50" },
    ]);
    actionButton("Scan Ticket", () =>
      openModal("Scan Ticket", [{ name: "ticket_number", label: "Ticket Number", required: true }], async (payload) => {
        const res = await api(`${apiBase}/boarding/scan/`, { method: "POST", body: JSON.stringify(payload) });
        showAlert(`Ticket valid: ${res.ticket_number || "OK"}`, "success");
      })
    );
    bindRowActions({
      confirm: async (row) => {
        await api(`${apiBase}/boarding/${row.id}/confirm/`, { method: "POST", body: JSON.stringify({}) });
        showAlert("Boarding confirmed", "success");
        await refreshCurrent();
      },
    });
  }

  async function loadStaff() {
    const data = await api(`${apiBase}/staff/`);
    state.data.staff = data;
    state.pageData = data.filter(filterBySearch);
    el.panelBody.innerHTML = tableFromArray(
      state.pageData,
      ["id", "user.name", "user.phone", "booking_permission", "boarding_permission", "finance_permission", "created_at"],
      [
        { id: "edit", label: "Edit", className: "bg-yellow-50" },
        { id: "delete", label: "Delete", className: "bg-red-50" },
      ]
    );
    actionButton("Add Staff", async () => {
      const users = await api(`${apiBase}/staff/available-users/`);
      openModal(
        "Create Staff",
        [
          { name: "user", label: `User ID (${users.length} available)`, required: true },
          { name: "booking_permission", label: "booking_permission(1/0)" },
          { name: "boarding_permission", label: "boarding_permission(1/0)" },
          { name: "finance_permission", label: "finance_permission(1/0)" },
        ],
        (payload) =>
          api(`${apiBase}/staff/create/`, {
            method: "POST",
            body: JSON.stringify({
              user: payload.user,
              booking_permission: payload.booking_permission === "1",
              boarding_permission: payload.boarding_permission === "1",
              finance_permission: payload.finance_permission === "1",
            }),
          })
      );
    });
    bindRowActions({
      edit: async (row) =>
        openModal(
          "Update Staff Permissions",
          [
            { name: "booking_permission", label: "Booking (1/0)", value: row.booking_permission ? "1" : "0" },
            { name: "boarding_permission", label: "Boarding (1/0)", value: row.boarding_permission ? "1" : "0" },
            { name: "finance_permission", label: "Finance (1/0)", value: row.finance_permission ? "1" : "0" },
          ],
          (payload) =>
            api(`${apiBase}/staff/${row.id}/`, {
              method: "PATCH",
              body: JSON.stringify({
                booking_permission: payload.booking_permission === "1",
                boarding_permission: payload.boarding_permission === "1",
                finance_permission: payload.finance_permission === "1",
              }),
            }),
          "Update"
        ),
      delete: async (row) => {
        if (!window.confirm("Delete staff member?")) return;
        await api(`${apiBase}/staff/${row.id}/`, { method: "DELETE" });
        showAlert("Staff removed", "success");
        await refreshCurrent();
      },
    });
  }

  async function loadAgents() {
    const data = await api(`${apiBase}/agents/`);
    state.data.agents = data;
    el.panelBody.innerHTML = tableFromArray(data.filter(filterBySearch), ["id", "user.name", "user.phone", "is_active", "created_at"]);
  }

  async function loadRevenue() {
    const [stats, history] = await Promise.all([api(`${apiBase}/revenue/stats/`), api(`${apiBase}/revenue/history/`)]);
    state.data.revenue = { stats, history };
    renderStats(stats);
    el.panelBody.innerHTML = tableFromArray(history.filter(filterBySearch), ["id", "transaction_type", "amount", "status", "description", "created_at"]);
  }

  function paymentMethodCanEdit(pmData) {
    if (!pmData) return true;
    if (typeof pmData.can_edit === "boolean") return pmData.can_edit;
    return pmData.status === "pending" || pmData.status === "rejected";
  }

  function paymentMethodFormFields(pmData) {
    const pt = pmData?.payment_method_type || "bank_account";
    const d = pmData?.payment_details || {};
    return [
      {
        name: "payment_method_type",
        label: "Method type",
        type: "select",
        required: true,
        options: [
          { value: "bank_account", label: "Bank account" },
          { value: "upi", label: "UPI" },
          { value: "wallet", label: "Wallet" },
        ],
        value: pt,
      },
      { name: "account_number", label: "Account number (bank)", value: d.account_number || "", helpText: "Required when type is Bank account" },
      { name: "ifsc", label: "IFSC (bank)", value: d.ifsc || "" },
      { name: "bank_name", label: "Bank name", value: d.bank_name || "" },
      { name: "account_holder_name", label: "Account holder name (bank)", value: d.account_holder_name || "" },
      { name: "vpa", label: "UPI VPA", value: d.vpa || d.upi_id || "", helpText: "Required when type is UPI" },
      { name: "wallet_type", label: "Wallet type (e.g. eSewa, Khalti)", value: d.wallet_type || "", helpText: "Required when type is Wallet" },
      { name: "wallet_id", label: "Wallet ID / phone", value: d.wallet_id || "" },
      { name: "wallet_provider", label: "Wallet provider (optional)", value: d.wallet_provider || "" },
    ];
  }

  function paymentMethodReadOnlyFields(pmData) {
    return paymentMethodFormFields(pmData).map((f) => ({ ...f, disabled: true, required: false }));
  }

  function buildPaymentMethodApiBody(payload) {
    const t = payload.payment_method_type;
    if (t === "bank_account") {
      const account_number = String(payload.account_number || "").trim();
      const ifsc = String(payload.ifsc || "").trim();
      const bank_name = String(payload.bank_name || "").trim();
      const account_holder_name = String(payload.account_holder_name || "").trim();
      if (!account_number || !ifsc || !bank_name || !account_holder_name) {
        throw new Error("Bank account: account number, IFSC, bank name, and account holder name are required.");
      }
      return {
        payment_method_type: "bank_account",
        payment_details: {
          account_number,
          ifsc: ifsc.toUpperCase(),
          bank_name,
          account_holder_name,
        },
      };
    }
    if (t === "upi") {
      const vpa = String(payload.vpa || "").trim();
      if (!vpa) throw new Error("UPI: VPA is required.");
      return { payment_method_type: "upi", payment_details: { vpa, upi_id: vpa } };
    }
    if (t === "wallet") {
      const wallet_type = String(payload.wallet_type || "").trim();
      const wallet_id = String(payload.wallet_id || "").trim();
      if (!wallet_type || !wallet_id) throw new Error("Wallet: type and wallet ID are required.");
      const wallet_provider = String(payload.wallet_provider || "").trim() || wallet_type;
      return { payment_method_type: "wallet", payment_details: { wallet_type, wallet_id, wallet_provider } };
    }
    throw new Error("Select a valid method type.");
  }

  async function loadWallet() {
    let pm = null;
    try {
      pm = await api(`${coreApiBase}/merchant/payment-method/`);
    } catch (_) {
      pm = { success: false, data: null };
    }
    const wd = await api(`${coreApiBase}/merchant/withdrawals/`).catch(() => ({ results: [] }));
    const pmData = pm && pm.success && pm.data ? pm.data : null;
    const canEditPm = paymentMethodCanEdit(pmData);
    const pmStatusLabel = pmData ? pmData.status_display || pmData.status || "—" : "Not configured";
    const pmValueDetail = pmData
      ? `${pmData.payment_method_type_display || pmData.payment_method_type || ""} — ${pmData.status_display || pmData.status || ""}${
          canEditPm ? "" : " (locked — contact admin to change)"
        }`
      : "No payout method on file. Add bank, UPI, or wallet for withdrawals.";
    const rows = [];
    rows.push({
      section: "payment_method",
      name: "Payment details",
      id: null,
      amount: null,
      status: pmStatusLabel,
      created_at: null,
      value: pmValueDetail,
    });
    (wd.results || wd.data || []).forEach((it) => rows.push(it));
    el.panelBody.innerHTML = tableFromArray(rows.filter(filterBySearch), ["section", "id", "amount", "status", "created_at", "value"]);

    if (pmData && !canEditPm) {
      actionButton(
        "View payment details",
        () => {
          openModal(
            "Payment method (approved)",
            paymentMethodReadOnlyFields(pmData),
            async () => {},
            "Close",
            { silentSuccess: true }
          );
        },
        "bg-gray-700 text-white px-3 py-2 rounded-lg text-sm"
      );
    }
    if (!pmData) {
      actionButton(
        "Add payment method",
        () =>
          openModal("Add payment method", paymentMethodFormFields(null), async (payload) => {
            const body = buildPaymentMethodApiBody(payload);
            await api(`${coreApiBase}/merchant/payment-method/create/`, { method: "POST", body: JSON.stringify(body) });
          }),
        "bg-red-600 text-white px-3 py-2 rounded-lg text-sm"
      );
    } else if (canEditPm) {
      actionButton(
        "Edit payment method",
        () =>
          openModal("Edit payment method", paymentMethodFormFields(pmData), async (payload) => {
            const body = buildPaymentMethodApiBody(payload);
            await api(`${coreApiBase}/merchant/payment-method/update/`, { method: "PUT", body: JSON.stringify(body) });
          }),
        "bg-red-600 text-white px-3 py-2 rounded-lg text-sm"
      );
      actionButton(
        "Delete payment method",
        async () => {
          if (!confirm("Delete your saved payment method? You can add a new one after.")) return;
          try {
            await api(`${coreApiBase}/merchant/payment-method/delete/`, { method: "DELETE" });
            showAlert("Payment method deleted.", "success");
            refreshCurrent();
          } catch (err) {
            showAlert(parseApiErrorMessage(err), "error");
          }
        },
        "bg-gray-700 text-white px-3 py-2 rounded-lg text-sm"
      );
    }
    actionButton("Create Withdrawal", () =>
      openModal("Withdrawal", [{ name: "amount", label: "Amount", type: "number", min: "0", step: "0.01", required: true }], (payload) =>
        api(`${coreApiBase}/merchant/withdrawals/create/`, { method: "POST", body: JSON.stringify(payload) })
      )
    );
  }

  async function createBookingFlow() {
    openModal(
      "Create Booking",
      [
        { name: "vehicle", label: "Vehicle ID", required: true },
        { name: "seat_ids", label: "Seat IDs comma separated", required: true },
        { name: "booking_date", label: "Booking DateTime (ISO)", required: true },
        { name: "name", label: "Passenger Name", required: true },
        { name: "phone", label: "Phone", required: true },
        { name: "gender", label: "Gender male/female", required: true },
        { name: "nationality", label: "Nationality" },
        { name: "remarks", label: "Remarks" },
      ],
      (payload) =>
        api(`${apiBase}/bookings/create/`, {
          method: "POST",
          body: JSON.stringify({
            ...payload,
            seat_ids: String(payload.seat_ids)
              .split(",")
              .map((x) => parseInt(x.trim(), 10))
              .filter(Boolean),
          }),
        })
    );
  }

  function filterBySearch(item) {
    if (!state.query) return true;
    return JSON.stringify(item).toLowerCase().includes(state.query.toLowerCase());
  }

  async function render() {
    clearAlert();
    drawMenu();
    el.panelActions.innerHTML = "";
    el.panelTitle.textContent = state.tab.replace("-", " ").toUpperCase();
    el.panelBody.innerHTML = `<div class="text-sm text-gray-500">Loading...</div>`;
    try {
      if (state.tab === "dashboard") return await loadDashboard();
      if (state.tab === "bookings") return await loadBookings();
      if (state.tab === "vehicles") return await loadVehicles();
      if (state.tab === "boarding") return await loadBoarding();
      if (state.tab === "staff") return await loadStaff();
      if (state.tab === "agents") return await loadAgents();
      if (state.tab === "revenue") return await loadRevenue();
      if (state.tab === "wallet") return await loadWallet();
      if (state.tab === "create-booking") return await createBookingFlow();
    } catch (err) {
      showAlert(err.message, "error");
      el.panelBody.innerHTML = `<div class="text-sm text-red-600">Failed to load data</div>`;
    }
  }

  async function bootstrapSession() {
    const session = await api(`${apiBase}/session/`);
    state.session = session;
    const allowed = {
      travel_committee: session.is_travel_committee,
      travel_staff: session.is_travel_staff,
      travel_dealer: session.is_travel_dealer,
      agent: session.is_agent,
    };
    if (!allowed[role]) {
      showAlert("Role mismatch. Redirecting to your allowed dashboard.", "warning");
      const dest = allowed.travel_committee
        ? "/app/travel-committee/"
        : allowed.travel_staff
        ? "/app/travel-committee-staff/"
        : allowed.travel_dealer
        ? "/app/travel-dealer/"
        : allowed.agent
        ? "/app/agent/"
        : "/dashboard/";
      setTimeout(() => (window.location.href = dest), 700);
      return false;
    }
    return true;
  }

  async function refreshCurrent() {
    await render();
  }

  function bindRowActions(actionMap) {
    const buttons = el.panelBody.querySelectorAll("button[data-row][data-act]");
    buttons.forEach((btn) => {
      btn.addEventListener("click", async () => {
        const row = state.pageData[parseInt(btn.dataset.row, 10)];
        const action = actionMap[btn.dataset.act];
        if (!row || !action) return;
        try {
          await action(row);
        } catch (err) {
          showAlert(err.message, "error");
        }
      });
    });
  }

  el.refreshBtn.addEventListener("click", refreshCurrent);
  el.searchInput.addEventListener("input", (e) => {
    state.query = e.target.value || "";
    render();
  });
  el.modalClose.addEventListener("click", closeModal);
  el.modalRoot.addEventListener("click", (e) => {
    if (e.target === el.modalRoot) closeModal();
  });

  (async function init() {
    try {
      const ok = await bootstrapSession();
      if (!ok) return;
      state.tab = tabsForRole()[0] || "dashboard";
      await render();
    } catch (err) {
      showAlert(err.message, "error");
    }
  })();
})();
