(() => {
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
  const scenarioList = window.SCENARIO_LIST || [];
  const mechanismList = window.MECHANISM_LIST || [];

  const elements = {
    appRoot: document.getElementById("app-root"),
    scenarioSelectWrap: document.getElementById("scenario-select-wrap"),
    scenarioSelect: document.getElementById("scenario-select"),
    scenarioDropdown: document.getElementById("scenario-dropdown"),
    scenarioTrigger: document.getElementById("scenario-trigger"),
    scenarioLabel: document.getElementById("scenario-label"),
    scenarioMenu: document.getElementById("scenario-menu"),
    mechanismSelectWrap: document.getElementById("mechanism-select-wrap"),
    mechanismSelect: document.getElementById("mechanism-select"),
    mechanismDropdown: document.getElementById("mechanism-dropdown"),
    mechanismTrigger: document.getElementById("mechanism-trigger"),
    mechanismLabel: document.getElementById("mechanism-label"),
    mechanismMenu: document.getElementById("mechanism-menu"),
    mechanismDesc: document.getElementById("mechanism-desc"),
    btnSidebarToggle: document.getElementById("btn-sidebar-toggle"),
    speedSlider: document.getElementById("speed-slider"),
    speedValue: document.getElementById("speed-value"),
    statusRunning: document.getElementById("status-running"),
    statusSimulation: document.getElementById("status-simulation"),
    statusProgress: document.getElementById("status-progress"),
    statusOrders: document.getElementById("status-orders"),
    gridCanvas: document.getElementById("grid-canvas"),
    chartOrders: document.getElementById("chart-orders"),
    chartDistance: document.getElementById("chart-distance"),
    chartBattery: document.getElementById("chart-battery"),
    chartConflicts: document.getElementById("chart-conflicts"),
    robotsTable: document.getElementById("robots-table-body"),
    ordersPending: document.getElementById("orders-pending"),
    ordersAssigned: document.getElementById("orders-assigned"),
    ordersCompleted: document.getElementById("orders-completed"),
    batchTable: document.getElementById("batch-table-body"),
    batchDownloads: document.getElementById("batch-downloads"),
    suiteResults: document.getElementById("suite-results"),
    suiteTableBody: document.getElementById("suite-table-body"),
    suiteProgress: document.getElementById("suite-progress-bar"),
    suiteStatus: document.getElementById("suite-status"),
    btnRunSuite: document.getElementById("btn-run-suite"),
    btnClearSuite: document.getElementById("btn-clear-suite"),
    btnRunBatch: document.getElementById("btn-run-batch"),
    btnReset: document.getElementById("btn-reset"),
    btnStep: document.getElementById("btn-step"),
    btnPlay: document.getElementById("btn-play"),
    btnPause: document.getElementById("btn-pause"),
    customParams: document.getElementById("custom-params"),
    numRobots: document.getElementById("num-robots"),
    numRobotsValue: document.getElementById("num-robots-value"),
    gridSize: document.getElementById("grid-size"),
    gridSizeValue: document.getElementById("grid-size-value"),
    maxSteps: document.getElementById("max-steps"),
    maxStepsValue: document.getElementById("max-steps-value"),
    orderMode: document.getElementById("order-mode"),
    orderModeDropdown: document.getElementById("order-mode-dropdown"),
    orderModeTrigger: document.getElementById("order-mode-trigger"),
    orderModeLabel: document.getElementById("order-mode-label"),
    orderModeMenu: document.getElementById("order-mode-menu"),
    orderCountRow: document.getElementById("order-count-row"),
    orderCount: document.getElementById("order-count"),
    orderCountValue: document.getElementById("order-count-value"),
    orderRateRow: document.getElementById("order-rate-row"),
    orderRate: document.getElementById("order-rate"),
    orderRateValue: document.getElementById("order-rate-value"),
    clusteredOrders: document.getElementById("clustered-orders"),
    clusterSettings: document.getElementById("cluster-settings"),
    clusterCenterX: document.getElementById("cluster-center-x"),
    clusterCenterY: document.getElementById("cluster-center-y"),
    clusterRadius: document.getElementById("cluster-radius"),
    clusterRadiusValue: document.getElementById("cluster-radius-value"),
    failureEnabled: document.getElementById("failure-enabled"),
    failureSettings: document.getElementById("failure-settings"),
    failureStep: document.getElementById("failure-step"),
    failureStepValue: document.getElementById("failure-step-value"),
  };

  let currentState = window.INIT_STATE || {};

  function postJson(url, data) {
    return fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(data || {}),
    }).then((res) => res.json());
  }

  function ensureOptions(select, options, formatter) {
    if (select.options.length > 0) {
      return;
    }
    options.forEach((item) => {
      const option = document.createElement("option");
      if (typeof item === "string") {
        option.value = item;
        option.textContent = item;
      } else {
        option.value = item.value;
        option.textContent = formatter ? formatter(item) : item.label;
      }
      select.appendChild(option);
    });
  }

  function ensureScenarioMenu() {
    if (!elements.scenarioMenu || elements.scenarioMenu.children.length > 0) {
      return;
    }
    scenarioList.forEach((item) => {
      const option = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "mechanism-option";
      button.dataset.value = item;
      button.setAttribute("role", "option");
      button.textContent = item;
      option.appendChild(button);
      elements.scenarioMenu.appendChild(option);
    });
  }

  function ensureMechanismMenu() {
    if (!elements.mechanismMenu || elements.mechanismMenu.children.length > 0) {
      return;
    }
    mechanismList.forEach((item) => {
      const value = typeof item === "string" ? item : item.value;
      const label = typeof item === "string" ? item : item.label;
      const option = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "mechanism-option";
      button.dataset.value = value;
      button.setAttribute("role", "option");
      button.textContent = label;
      option.appendChild(button);
      elements.mechanismMenu.appendChild(option);
    });
  }

  function ensureOrderModeMenu() {
    if (!elements.orderModeMenu || elements.orderModeMenu.children.length > 0) {
      return;
    }
    Array.from(elements.orderMode.options).forEach((optionEl) => {
      const option = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "mechanism-option";
      button.dataset.value = optionEl.value;
      button.setAttribute("role", "option");
      button.textContent = optionEl.textContent;
      option.appendChild(button);
      elements.orderModeMenu.appendChild(option);
    });
  }

  function getMechanismValue(item) {
    return typeof item === "string" ? item : item?.value;
  }

  function updateScenarioSelection(value) {
    if (!elements.scenarioMenu) {
      return;
    }
    elements.scenarioMenu.querySelectorAll(".mechanism-option").forEach((button) => {
      const isSelected = button.dataset.value === value;
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-selected", isSelected ? "true" : "false");
    });
  }

  function updateMechanismSelection(value) {
    if (!elements.mechanismMenu) {
      return;
    }
    elements.mechanismMenu.querySelectorAll(".mechanism-option").forEach((button) => {
      const isSelected = button.dataset.value === value;
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-selected", isSelected ? "true" : "false");
    });
  }

  function updateOrderModeSelection(value) {
    if (!elements.orderModeMenu) {
      return;
    }
    elements.orderModeMenu.querySelectorAll(".mechanism-option").forEach((button) => {
      const isSelected = button.dataset.value === value;
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-selected", isSelected ? "true" : "false");
    });
  }

  function setOrderModeValue(value) {
    if (!value) {
      return;
    }
    elements.orderMode.value = value;
    const option = Array.from(elements.orderMode.options).find((opt) => opt.value === value);
    if (elements.orderModeLabel) {
      elements.orderModeLabel.textContent = option ? option.textContent : value;
    }
    updateOrderModeSelection(value);
  }

  function setMechanismValue(value, { post } = {}) {
    if (!value) {
      return;
    }
    elements.mechanismSelect.value = value;
    const mech = mechanismList.find((item) => (typeof item === "string" ? item === value : item.value === value));
    const label = typeof mech === "string" ? mech : mech?.label;
    if (elements.mechanismLabel) {
      elements.mechanismLabel.textContent = label || value;
    }
    if (elements.mechanismDesc) {
      elements.mechanismDesc.textContent = mech && typeof mech !== "string" ? mech.description : "Select a mechanism";
    }
    updateMechanismSelection(value);
    if (post) {
      postJson("/api/config", { mechanism: value }).then(applyState);
    }
  }

  function setScenarioValue(value, { post } = {}) {
    if (!value) {
      return;
    }
    elements.scenarioSelect.value = value;
    if (elements.scenarioLabel) {
      elements.scenarioLabel.textContent = value;
    }
    updateScenarioSelection(value);
    if (post) {
      postJson("/api/config", { scenario: value }).then(applyState);
    }
  }

  function setMechanismMenuOpen(open) {
    if (!elements.mechanismDropdown || !elements.mechanismTrigger) {
      return;
    }
    elements.mechanismDropdown.classList.toggle("is-open", open);
    if (elements.mechanismSelectWrap) {
      elements.mechanismSelectWrap.classList.toggle("is-open", open);
    }
    elements.mechanismTrigger.setAttribute("aria-expanded", open ? "true" : "false");
    if (!open) {
      elements.mechanismTrigger.blur();
    }
    if (open && elements.mechanismMenu) {
      const active = elements.mechanismMenu.querySelector(".mechanism-option.is-selected");
      if (active) {
        active.scrollIntoView({ block: "nearest" });
      }
    }
  }

  function setScenarioMenuOpen(open) {
    if (!elements.scenarioDropdown || !elements.scenarioTrigger) {
      return;
    }
    elements.scenarioDropdown.classList.toggle("is-open", open);
    if (elements.scenarioSelectWrap) {
      elements.scenarioSelectWrap.classList.toggle("is-open", open);
    }
    elements.scenarioTrigger.setAttribute("aria-expanded", open ? "true" : "false");
    if (open && elements.scenarioMenu) {
      const active = elements.scenarioMenu.querySelector(".mechanism-option.is-selected");
      if (active) {
        active.scrollIntoView({ block: "nearest" });
      }
    }
  }

  function setOrderModeMenuOpen(open) {
    if (!elements.orderModeDropdown || !elements.orderModeTrigger) {
      return;
    }
    elements.orderModeDropdown.classList.toggle("is-open", open);
    const orderModeWrap = elements.orderModeDropdown.closest(".order-mode-wrap");
    if (orderModeWrap) {
      orderModeWrap.classList.toggle("is-open", open);
    }
    elements.orderModeTrigger.setAttribute("aria-expanded", open ? "true" : "false");
    if (open && elements.orderModeMenu) {
      const active = elements.orderModeMenu.querySelector(".mechanism-option.is-selected");
      if (active) {
        active.scrollIntoView({ block: "nearest" });
      }
    }
  }

  function applyState(data) {
    if (!data) {
      return;
    }
    currentState = data;
    updateConfig(data.config || {});
    updateStatus(data);
    updateMetrics(data.metrics || {});
    updateCharts(data.metrics_history || []);
    updateRobots(data.robots || []);
    updateOrders(data.orders || {});
    updateBatch(data.batch_results || []);
    updateSuite(data.suite_status || {}, data.suite_results || []);
    drawGrid(data.snapshot || {});
  }

  function updateConfig(config) {
    ensureOptions(elements.scenarioSelect, scenarioList);
    ensureOptions(elements.mechanismSelect, mechanismList, (item) => item.label);
    ensureScenarioMenu();
    ensureMechanismMenu();
    ensureOrderModeMenu();

    const selectedScenario = config.selected_scenario || scenarioList[0];
    const selectedMechanism = config.mechanism || getMechanismValue(mechanismList[0]);

    setScenarioValue(selectedScenario, { post: false });
    setMechanismValue(selectedMechanism, { post: false });


    const params = config.active_params || {};
    elements.numRobots.value = params.num_robots ?? 5;
    elements.numRobotsValue.textContent = elements.numRobots.value;

    elements.gridSize.value = params.grid_size ?? 20;
    elements.gridSizeValue.textContent = elements.gridSize.value;

    elements.maxSteps.value = params.max_steps ?? 200;
    elements.maxStepsValue.textContent = elements.maxSteps.value;

    setOrderModeValue(params.order_mode || "fixed_orders");
    updateOrderMode();

    elements.orderCount.value = params.order_count ?? 20;
    elements.orderCountValue.textContent = elements.orderCount.value;

    elements.orderRate.value = params.order_rate ?? 0.3;
    elements.orderRateValue.textContent = Number(elements.orderRate.value).toFixed(2);

    elements.clusteredOrders.checked = Boolean(params.clustered_orders);
    updateClusterSettings();

    elements.clusterCenterX.max = (params.grid_size ?? 20) - 1;
    elements.clusterCenterY.max = (params.grid_size ?? 20) - 1;
    elements.clusterCenterX.value = params.cluster_center_x ?? 10;
    elements.clusterCenterY.value = params.cluster_center_y ?? 10;

    elements.clusterRadius.value = params.cluster_radius ?? 5;
    elements.clusterRadiusValue.textContent = elements.clusterRadius.value;

    const failureStep = params.robot_failure_step;
    elements.failureEnabled.checked = failureStep !== null && failureStep !== undefined;
    elements.failureStep.value = failureStep ?? 80;
    elements.failureStep.max = elements.maxSteps.value;
    elements.failureStepValue.textContent = elements.failureStep.value;
    updateFailureSettings();

    elements.speedSlider.value = config.speed ?? 5;
    elements.speedValue.textContent = elements.speedSlider.value;
  }

  function updateStatus(data) {
    elements.statusRunning.textContent = data.running ? "Running" : "Paused";
    elements.statusSimulation.textContent = data.model_running ? "Active" : "Finished";
    elements.statusProgress.textContent = `${data.step_count || 0} steps @ ${data.config?.speed ?? 0}x`;

    const orders = data.orders || {};
    const pending = orders.pending ? orders.pending.length : 0;
    const assigned = orders.assigned ? orders.assigned.length : 0;
    const completed = orders.completed ? orders.completed.length : 0;
    elements.statusOrders.textContent = `${pending} pending | ${assigned} assigned | ${completed} completed`;
  }

  function formatNumber(value, decimals) {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return "-";
    }
    if (typeof value === "number") {
      return value.toFixed(decimals ?? 0);
    }
    return value;
  }

  function updateMetric(idValue, idStatus, value, statusClass, statusLabel, decimals) {
    const valueEl = document.getElementById(idValue);
    if (valueEl) {
      valueEl.textContent = formatNumber(value, decimals);
    }
    const statusEl = document.getElementById(idStatus);
    if (statusEl) {
      statusEl.className = `metric-status ${statusClass}`;
      statusEl.textContent = statusLabel;
    }
  }

  function updateMetrics(metrics) {
    updateMetric("metric-orders-generated", "metric-status-orders-generated", metrics.orders_generated, "status-ok", "OK");
    updateMetric("metric-orders-completed", "metric-status-orders-completed", metrics.orders_completed, "status-ok", "OK");
    updateMetric("metric-active-orders", "metric-status-active-orders", metrics.active_orders, "status-ok", "OK");
    updateMetric("metric-throughput", "metric-status-throughput", metrics.throughput, "status-ok", "OK", 4);
    updateMetric("metric-efficiency", "metric-status-efficiency", metrics.efficiency, "status-ok", "OK", 4);
    updateMetric("metric-total-distance", "metric-status-total-distance", metrics.total_distance, "status-ok", "OK", 1);
    updateMetric("metric-avg-battery", "metric-status-avg-battery", metrics.avg_battery, "status-ok", "OK", 1);

    const conflicts = metrics.attempted_conflicts || 0;
    const conflictStatus = conflicts > 10 ? ["status-alert", "Alert"] : conflicts > 5 ? ["status-warning", "Watch"] : ["status-ok", "OK"];
    updateMetric("metric-conflicts", "metric-status-conflicts", conflicts, conflictStatus[0], conflictStatus[1]);

    updateMetric("metric-hard-blocks", "metric-status-hard-blocks", metrics.hard_blocks, "status-ok", "OK");
    updateMetric("metric-idle-robots", "metric-status-idle-robots", metrics.idle_robots, "status-ok", "OK");

    const broken = metrics.broken_robots || 0;
    const brokenStatus = broken > 0 ? ["status-alert", "Alert"] : ["status-ok", "OK"];
    updateMetric("metric-broken-robots", "metric-status-broken-robots", broken, brokenStatus[0], brokenStatus[1]);

    updateMetric("metric-fairness-var", "metric-status-fairness-var", metrics.fairness_variance, "status-ok", "OK", 2);
  }

  function updateCharts(history) {
    const data = history || [];
    const ordersCompleted = data.map((row) => row.orders_completed || 0);
    const activeOrders = data.map((row) => row.active_orders || 0);
    const totalDistance = data.map((row) => row.total_distance || 0);
    const avgBattery = data.map((row) => row.avg_battery || 0);
    const conflicts = data.map((row) => row.attempted_conflicts || 0);
    const hardBlocks = data.map((row) => row.hard_blocks || 0);
    const totalConflicts = data.map((row) => row.total_conflicts || 0);

    drawLineChart(elements.chartOrders, [
      { label: "Orders Completed", data: ordersCompleted, color: "#3b82f6" },
      { label: "Active Orders", data: activeOrders, color: "#10b981" },
    ]);

    drawLineChart(elements.chartDistance, [
      { label: "Total Distance", data: totalDistance, color: "#f59e0b" },
    ]);

    drawLineChart(elements.chartBattery, [
      { label: "Avg Battery", data: avgBattery, color: "#3b82f6" },
    ]);

    drawLineChart(elements.chartConflicts, [
      { label: "Attempted Conflicts", data: conflicts, color: "#ef4444" },
      { label: "Hard Blocks", data: hardBlocks, color: "#f59e0b" },
      { label: "Total Conflicts", data: totalConflicts, color: "#8b5cf6" },
    ]);
  }

  function updateRobots(robots) {
    elements.robotsTable.innerHTML = "";
    if (!robots.length) {
      return;
    }

    robots.forEach((robot) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${robot.id}</td>
        <td>${renderStateBadge(robot.state)}</td>
        <td>${robot.battery}%</td>
        <td>${robot.tasks_completed}</td>
        <td>${robot.distance}</td>
        <td>${robot.conflicts}</td>
        <td>${robot.hard_blocks}</td>
        <td>${robot.current_task}</td>
        <td>${robot.target}</td>
      `;
      elements.robotsTable.appendChild(row);
    });
  }

  function updateOrders(orders) {
    updateOrderList(elements.ordersPending, orders.pending || [], (o) => `#${o.id}: ${o.pickup} -> ${o.delivery}`);
    updateOrderList(elements.ordersAssigned, orders.assigned || [], (o) => `#${o.id}: ${o.pickup} -> ${o.delivery}`);
    updateOrderList(elements.ordersCompleted, orders.completed || [], (o) => `#${o.id}: delay=${o.delay} steps`);
  }

  function updateOrderList(container, items, formatter) {
    container.innerHTML = "";
    if (!items.length) {
      const li = document.createElement("li");
      li.textContent = "No orders";
      container.appendChild(li);
      return;
    }
    items.slice(0, 10).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = formatter(item);
      container.appendChild(li);
    });
  }

  function updateBatch(batchResults) {
    elements.batchTable.innerHTML = "";
    if (!batchResults.length) {
      if (elements.batchDownloads) {
        elements.batchDownloads.classList.add("hidden");
      }
      return;
    }

    if (elements.batchDownloads) {
      elements.batchDownloads.classList.remove("hidden");
    }

    batchResults.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.mechanism}</td>
        <td>${Number(row.throughput).toFixed(4)}</td>
        <td>${Number(row.efficiency).toFixed(4)}</td>
        <td>${Number(row.total_distance).toFixed(1)}</td>
        <td>${row.total_conflicts}</td>
        <td>${Number(row.fairness_variance).toFixed(2)}</td>
      `;
      elements.batchTable.appendChild(tr);
    });
  }

  function updateSuite(status, summary) {
    if (summary.length) {
      elements.suiteResults.classList.remove("hidden");
      elements.suiteTableBody.innerHTML = "";
      summary.forEach((row) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${row.Scenario}</td>
          <td>${row.Mechanism}</td>
          <td>${Number(row.Throughput).toFixed(4)}</td>
          <td>${Number(row.Efficiency).toFixed(4)}</td>
          <td>${Number(row.Total_Distance).toFixed(1)}</td>
          <td>${row.Total_Conflicts}</td>
          <td>${Number(row.Fairness_Variance).toFixed(2)}</td>
        `;
        elements.suiteTableBody.appendChild(tr);
      });
    } else {
      elements.suiteResults.classList.add("hidden");
    }

    const progress = Math.min(100, Math.max(0, (status.progress || 0) * 100));
    elements.suiteProgress.style.width = `${progress}%`;
    elements.suiteStatus.textContent = status.status || "Idle";
    elements.btnRunSuite.disabled = Boolean(status.running);
  }

  function drawLineChart(canvas, series) {
    if (!canvas) {
      return;
    }
    const ctx = canvas.getContext("2d");
    const width = canvas.clientWidth;
    const height = canvas.clientHeight || 220;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    ctx.scale(ratio, ratio);

    ctx.clearRect(0, 0, width, height);
    const background = ctx.createLinearGradient(0, 0, 0, height);
    background.addColorStop(0, "#ffffff");
    background.addColorStop(1, "#f1f5f9");
    ctx.fillStyle = background;
    ctx.fillRect(0, 0, width, height);

    const padding = 34;
    ctx.font = "11px Bahnschrift, Trebuchet MS, sans-serif";
    const legendItems = series.map((line) => {
      const textWidth = ctx.measureText(line.label).width;
      const itemWidth = 10 + 6 + textWidth + 12;
      return { label: line.label, color: line.color, width: itemWidth };
    });
    const availableLegendWidth = Math.max(80, width - padding * 2);
    const legendRowHeight = 18;
    const legendPaddingTop = 8;
    let legendRowCount = 1;
    let rowWidth = 0;
    legendItems.forEach((item) => {
      if (rowWidth + item.width > availableLegendWidth && rowWidth > 0) {
        legendRowCount += 1;
        rowWidth = 0;
      }
      rowWidth += item.width;
    });
    const legendHeight = legendRowCount * legendRowHeight + legendPaddingTop + 6;
    const chartBottom = height - padding - legendHeight;
    const chartWidth = width - padding * 2;
    const chartHeight = chartBottom - padding;

    const allValues = series.flatMap((s) => s.data || []);
    if (!allValues.length) {
      ctx.fillStyle = "#94a3b8";
      ctx.font = "12px Bahnschrift, Trebuchet MS, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("No data yet", width / 2, height / 2);
      return;
    }

    let maxValue = Math.max(...allValues);
    let minValue = Math.min(...allValues);
    const range = maxValue - minValue || 1;
    maxValue += range * 0.1;
    minValue -= range * 0.1;

    ctx.strokeStyle = "rgba(148, 163, 184, 0.4)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i += 1) {
      const y = padding + (chartHeight / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }
    for (let i = 0; i <= 4; i += 1) {
      const x = padding + (chartWidth / 4) * i;
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, chartBottom);
      ctx.stroke();
    }

    const xCount = Math.max(...series.map((line) => (line.data || []).length));
    const xStep = xCount <= 10 ? 1 : xCount <= 20 ? 2 : xCount <= 50 ? 5 : 10;
    const yStepCount = 4;
    const yRange = maxValue - minValue || 1;
    const yDecimals = yRange >= 20 ? 0 : yRange >= 5 ? 1 : 2;

    ctx.fillStyle = "#64748b";
    ctx.font = "10px Bahnschrift, Trebuchet MS, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let x = 0; x < xCount; x += xStep) {
      const tx = padding + (chartWidth * x) / Math.max(1, xCount - 1);
      ctx.fillText(String(x), tx, chartBottom + 6);
    }
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let i = 0; i <= yStepCount; i += 1) {
      const value = maxValue - (yRange / yStepCount) * i;
      const ty = padding + (chartHeight / yStepCount) * i;
      ctx.fillText(value.toFixed(yDecimals), padding - 6, ty);
    }

    series.forEach((line) => {
      const data = line.data || [];
      if (data.length === 0) {
        return;
      }
      const points = data.map((value, index) => {
        const x = padding + (chartWidth * index) / Math.max(1, data.length - 1);
        const normalized = (value - minValue) / (maxValue - minValue || 1);
        const y = padding + chartHeight - normalized * chartHeight;
        return { x, y };
      });

      const fillGradient = ctx.createLinearGradient(0, padding, 0, height - padding);
      fillGradient.addColorStop(0, hexToRgba(line.color, 0.25));
      fillGradient.addColorStop(1, hexToRgba(line.color, 0.0));
      ctx.beginPath();
      points.forEach((point, index) => {
        if (index === 0) {
          ctx.moveTo(point.x, point.y);
        } else {
          ctx.lineTo(point.x, point.y);
        }
      });
      ctx.lineTo(points[points.length - 1].x, chartBottom);
      ctx.lineTo(points[0].x, chartBottom);
      ctx.closePath();
      ctx.fillStyle = fillGradient;
      ctx.fill();

      ctx.strokeStyle = line.color;
      ctx.lineWidth = 2.5;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.beginPath();
      points.forEach((point, index) => {
        if (index === 0) {
          ctx.moveTo(point.x, point.y);
        } else {
          ctx.lineTo(point.x, point.y);
        }
      });
      ctx.stroke();

      const lastPoint = points[points.length - 1];
      ctx.fillStyle = "#ffffff";
      ctx.strokeStyle = line.color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(lastPoint.x, lastPoint.y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    });

    ctx.font = "11px Bahnschrift, Trebuchet MS, sans-serif";
    ctx.textBaseline = "middle";
    ctx.textAlign = "left";
    let legendX = padding;
    let legendY = chartBottom + 20 + legendPaddingTop;
    legendItems.forEach((item) => {
      if (legendX + item.width > width - padding && legendX > padding) {
        legendX = padding;
        legendY += legendRowHeight;
      }
      ctx.fillStyle = item.color;
      ctx.fillRect(legendX, legendY - 6, 10, 10);
      ctx.strokeStyle = "#e2e8f0";
      ctx.lineWidth = 1;
      ctx.strokeRect(legendX, legendY - 6, 10, 10);
      ctx.fillStyle = "#475569";
      ctx.fillText(item.label, legendX + 16, legendY);
      legendX += item.width;
    });
  }

  function hexToRgba(hex, alpha) {
    const value = hex.replace("#", "");
    if (value.length !== 6) {
      return `rgba(59, 130, 246, ${alpha})`;
    }
    const r = parseInt(value.slice(0, 2), 16);
    const g = parseInt(value.slice(2, 4), 16);
    const b = parseInt(value.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }


  function drawGrid(snapshot) {
    if (!snapshot.grid_size) {
      return;
    }

    const [gridW, gridH] = snapshot.grid_size;
    const canvas = elements.gridCanvas;
    const ctx = canvas.getContext("2d");
    const containerWidth = canvas.parentElement.clientWidth;
    const size = Math.max(320, Math.min(containerWidth, 640));
    const ratio = window.devicePixelRatio || 1;
    canvas.width = size * ratio;
    canvas.height = size * ratio;
    canvas.style.height = `${size}px`;
    ctx.scale(ratio, ratio);

    ctx.clearRect(0, 0, size, size);
    ctx.fillStyle = "#fcfdff";
    ctx.fillRect(0, 0, size, size);

    const padding = 28;
    const innerSize = size - padding * 2;
    const cell = innerSize / Math.max(gridW, gridH);

    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 0.5;
    for (let x = 0; x <= gridW; x += 1) {
      ctx.beginPath();
      ctx.moveTo(padding + x * cell, padding);
      ctx.lineTo(padding + x * cell, padding + gridH * cell);
      ctx.stroke();
    }
    for (let y = 0; y <= gridH; y += 1) {
      ctx.beginPath();
      ctx.moveTo(padding, padding + y * cell);
      ctx.lineTo(padding + gridW * cell, padding + y * cell);
      ctx.stroke();
    }

    function toCanvas(pos) {
      return {
        x: padding + pos[0] * cell,
        y: padding + (gridH - 1 - pos[1]) * cell,
      };
    }

    const maxDim = Math.max(gridW, gridH);
    const tickStep = maxDim <= 12 ? 1 : maxDim <= 20 ? 2 : maxDim <= 30 ? 3 : 5;
    ctx.fillStyle = "#64748b";
    ctx.font = "10px Bahnschrift, Trebuchet MS, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let x = 0; x < gridW; x += tickStep) {
      const tx = padding + x * cell + cell * 0.5;
      ctx.fillText(String(x), tx, padding + innerSize + 6);
    }
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let y = 0; y < gridH; y += tickStep) {
      const ty = padding + (gridH - 1 - y) * cell + cell * 0.5;
      ctx.fillText(String(y), padding - 6, ty);
    }


    snapshot.shelves.forEach((shelf) => {
      const p = toCanvas(shelf.pos);
      ctx.fillStyle = "#cbd5e1";
      ctx.strokeStyle = "#94a3b8";
      ctx.lineWidth = 1;
      ctx.fillRect(p.x + cell * 0.1, p.y + cell * 0.1, cell * 0.8, cell * 0.8);
      ctx.strokeRect(p.x + cell * 0.1, p.y + cell * 0.1, cell * 0.8, cell * 0.8);
    });

    snapshot.stations.forEach((station) => {
      const p = toCanvas(station.pos);
      ctx.fillStyle = "#14b8a6";
      ctx.strokeStyle = "#0f766e";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(p.x + cell * 0.5, p.y + cell * 0.15);
      ctx.lineTo(p.x + cell * 0.15, p.y + cell * 0.85);
      ctx.lineTo(p.x + cell * 0.85, p.y + cell * 0.85);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });

    snapshot.orders.forEach((order) => {
      if (order.completed) {
        return;
      }
      const pickup = toCanvas(order.pickup);
      const delivery = toCanvas(order.delivery);

      if (order.assigned) {
        ctx.fillStyle = "#22c55e";
        ctx.fillRect(pickup.x + cell * 0.25, pickup.y + cell * 0.25, cell * 0.5, cell * 0.5);

        ctx.fillStyle = "#f97316";
        ctx.beginPath();
        ctx.moveTo(delivery.x + cell * 0.5, delivery.y + cell * 0.15);
        ctx.lineTo(delivery.x + cell * 0.15, delivery.y + cell * 0.85);
        ctx.lineTo(delivery.x + cell * 0.85, delivery.y + cell * 0.85);
        ctx.closePath();
        ctx.fill();
      } else {
        ctx.strokeStyle = "#3b82f6";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(pickup.x + cell * 0.5, pickup.y + cell * 0.5, cell * 0.3, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = "#ef4444";
        ctx.beginPath();
        ctx.moveTo(delivery.x + cell * 0.5, delivery.y + cell * 0.2);
        ctx.lineTo(delivery.x + cell * 0.2, delivery.y + cell * 0.8);
        ctx.lineTo(delivery.x + cell * 0.8, delivery.y + cell * 0.8);
        ctx.closePath();
        ctx.stroke();
      }
    });

    snapshot.robots.forEach((robot) => {
      const p = toCanvas(robot.pos);
      const color = stateColor(robot.state);
      ctx.fillStyle = color;
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(p.x + cell * 0.5, p.y + cell * 0.5, cell * 0.35, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#ffffff";
      ctx.font = `${Math.max(8, cell * 0.3)}px Bahnschrift, Trebuchet MS, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(robot.id), p.x + cell * 0.5, p.y + cell * 0.5);

      if (robot.target) {
        const t = toCanvas(robot.target);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        ctx.moveTo(p.x + cell * 0.5, p.y + cell * 0.5);
        ctx.lineTo(t.x + cell * 0.5, t.y + cell * 0.5);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(t.x + cell * 0.35, t.y + cell * 0.35);
        ctx.lineTo(t.x + cell * 0.65, t.y + cell * 0.65);
        ctx.moveTo(t.x + cell * 0.65, t.y + cell * 0.35);
        ctx.lineTo(t.x + cell * 0.35, t.y + cell * 0.65);
        ctx.stroke();
      }
    });
  }

  function stateColor(state) {
    const colors = {
      idle: "#6b7280",
      moving_to_pickup: "#0ea5a4",
      moving_to_delivery: "#16a34a",
      recharging: "#f59e0b",
      broken: "#dc2626",
    };
    return colors[state] || "#6b7280";
  }

  function renderStateBadge(state) {
    const map = {
      idle: "badge-idle",
      moving_to_pickup: "badge-pickup",
      moving_to_delivery: "badge-delivery",
      recharging: "badge-recharge",
      broken: "badge-broken",
    };
    const label = state.replace(/_/g, " ");
    const klass = map[state] || "badge-idle";
    return `<span class="state-badge ${klass}">${label}</span>`;
  }

  function updateOrderMode() {
    const mode = elements.orderMode.value;
    if (mode === "fixed_orders") {
      elements.orderCountRow.style.display = "grid";
      elements.orderRateRow.style.display = "none";
    } else {
      elements.orderCountRow.style.display = "none";
      elements.orderRateRow.style.display = "grid";
    }
  }

  function updateClusterSettings() {
    elements.clusterSettings.style.display = elements.clusteredOrders.checked ? "block" : "none";
  }

  function updateFailureSettings() {
    elements.failureSettings.style.display = elements.failureEnabled.checked ? "grid" : "none";
  }

  function collectParams() {
    return {
      num_robots: parseInt(elements.numRobots.value, 10),
      grid_size: parseInt(elements.gridSize.value, 10),
      max_steps: parseInt(elements.maxSteps.value, 10),
      order_mode: elements.orderMode.value,
      order_count: parseInt(elements.orderCount.value, 10),
      order_rate: parseFloat(elements.orderRate.value),
      clustered_orders: elements.clusteredOrders.checked,
      cluster_center_x: parseInt(elements.clusterCenterX.value, 10),
      cluster_center_y: parseInt(elements.clusterCenterY.value, 10),
      cluster_radius: parseInt(elements.clusterRadius.value, 10),
      robot_failure_step: elements.failureEnabled.checked ? parseInt(elements.failureStep.value, 10) : null,
    };
  }

  function bindControls() {
    initSidebarToggle();

    if (elements.scenarioTrigger && elements.scenarioMenu && elements.scenarioDropdown) {
      elements.scenarioTrigger.addEventListener("click", () => {
        const isOpen = elements.scenarioDropdown.classList.contains("is-open");
        setScenarioMenuOpen(!isOpen);
      });

      elements.scenarioTrigger.addEventListener("keydown", (event) => {
        if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          setScenarioMenuOpen(true);
        }
      });

      elements.scenarioMenu.addEventListener("click", (event) => {
        const button = event.target.closest(".mechanism-option");
        if (!button) {
          return;
        }
        const value = button.dataset.value;
        setScenarioMenuOpen(false);
        setScenarioValue(value, { post: true });
      });
    } else {
      elements.scenarioSelect.addEventListener("change", () => {
        postJson("/api/config", { scenario: elements.scenarioSelect.value }).then(applyState);
      });
    }

    if (elements.mechanismTrigger && elements.mechanismMenu && elements.mechanismDropdown) {
      elements.mechanismTrigger.addEventListener("click", () => {
        const isOpen = elements.mechanismDropdown.classList.contains("is-open");
        setMechanismMenuOpen(!isOpen);
      });

      elements.mechanismTrigger.addEventListener("keydown", (event) => {
        if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          setMechanismMenuOpen(true);
        }
      });

      elements.mechanismMenu.addEventListener("click", (event) => {
        const button = event.target.closest(".mechanism-option");
        if (!button) {
          return;
        }
        const value = button.dataset.value;
        setMechanismMenuOpen(false);
        setMechanismValue(value, { post: true });
      });
    }

    if (elements.orderModeTrigger && elements.orderModeMenu && elements.orderModeDropdown) {
      elements.orderModeTrigger.addEventListener("click", () => {
        const isOpen = elements.orderModeDropdown.classList.contains("is-open");
        setOrderModeMenuOpen(!isOpen);
      });

      elements.orderModeTrigger.addEventListener("keydown", (event) => {
        if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          setOrderModeMenuOpen(true);
        }
      });

      elements.orderModeMenu.addEventListener("click", (event) => {
        const button = event.target.closest(".mechanism-option");
        if (!button) {
          return;
        }
        const value = button.dataset.value;
        setOrderModeMenuOpen(false);
        setOrderModeValue(value);
        postJson("/api/config", { params: collectParams() }).then(applyState);
      });
    }

    document.addEventListener("click", (event) => {
      if (elements.scenarioDropdown && !elements.scenarioDropdown.contains(event.target)) {
        setScenarioMenuOpen(false);
      }
      if (elements.mechanismDropdown && !elements.mechanismDropdown.contains(event.target)) {
        setMechanismMenuOpen(false);
      }
      if (elements.orderModeDropdown && !elements.orderModeDropdown.contains(event.target)) {
        setOrderModeMenuOpen(false);
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        setScenarioMenuOpen(false);
        setMechanismMenuOpen(false);
        setOrderModeMenuOpen(false);
      }
    });

    elements.speedSlider.addEventListener("input", () => {
      elements.speedValue.textContent = elements.speedSlider.value;
      postJson("/api/config", { speed: elements.speedSlider.value }).then(applyState);
    });

    const paramInputs = [
      elements.numRobots,
      elements.gridSize,
      elements.maxSteps,
      elements.orderMode,
      elements.orderCount,
      elements.orderRate,
      elements.clusteredOrders,
      elements.clusterCenterX,
      elements.clusterCenterY,
      elements.clusterRadius,
      elements.failureEnabled,
      elements.failureStep,
    ];

    paramInputs.forEach((input) => {
      input.addEventListener("input", () => {
        elements.numRobotsValue.textContent = elements.numRobots.value;
        elements.gridSizeValue.textContent = elements.gridSize.value;
        elements.maxStepsValue.textContent = elements.maxSteps.value;
        elements.orderCountValue.textContent = elements.orderCount.value;
        elements.orderRateValue.textContent = Number(elements.orderRate.value).toFixed(2);
        elements.clusterRadiusValue.textContent = elements.clusterRadius.value;
        elements.failureStepValue.textContent = elements.failureStep.value;
        updateOrderMode();
        updateClusterSettings();
        updateFailureSettings();
      });

      input.addEventListener("change", () => {
        postJson("/api/config", { params: collectParams() }).then(applyState);
      });
    });

    elements.btnReset.addEventListener("click", () => {
      postJson("/api/control", { action: "reset" }).then(applyState);
    });

    elements.btnStep.addEventListener("click", () => {
      postJson("/api/control", { action: "step" }).then(applyState);
    });

    elements.btnPlay.addEventListener("click", () => {
      postJson("/api/control", { action: "play" }).then(applyState);
    });

    elements.btnPause.addEventListener("click", () => {
      postJson("/api/control", { action: "pause" }).then(applyState);
    });

    elements.btnRunBatch.addEventListener("click", () => {
      postJson("/api/run-batch", {}).then(applyState);
    });

    elements.btnRunSuite.addEventListener("click", () => {
      postJson("/api/run-suite", {}).then(applyState);
    });

    elements.btnClearSuite.addEventListener("click", () => {
      postJson("/api/clear-suite", {}).then(applyState);
    });

    document.querySelectorAll(".tab-button").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".tab-button").forEach((btn) => btn.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
        button.classList.add("active");
        const tab = button.getAttribute("data-tab");
        document.getElementById(`tab-${tab}`).classList.add("active");
      });
    });
  }

  function initSidebarToggle() {
    if (!elements.appRoot || !elements.btnSidebarToggle) {
      return;
    }
    const saved = safeGetItem("sidebar-collapsed");
    const collapsed = saved === "1";
    setSidebarCollapsed(collapsed);

    elements.btnSidebarToggle.addEventListener("click", () => {
      const isCollapsed = elements.appRoot.classList.contains("sidebar-collapsed");
      setSidebarCollapsed(!isCollapsed);
    });
  }

  function setSidebarCollapsed(collapsed) {
    elements.appRoot.classList.toggle("sidebar-collapsed", collapsed);
    safeSetItem("sidebar-collapsed", collapsed ? "1" : "0");
    if (elements.btnSidebarToggle) {
      const label = collapsed ? "Expand sidebar" : "Collapse sidebar";
      elements.btnSidebarToggle.setAttribute("aria-label", label);
      elements.btnSidebarToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      elements.btnSidebarToggle.setAttribute("title", label);
    }
  }

  function safeGetItem(key) {
    try {
      return localStorage.getItem(key);
    } catch (err) {
      return null;
    }
  }

  function safeSetItem(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (err) {
      // Ignore storage failures.
    }
  }

  function startPolling() {
    setInterval(() => {
      postJson("/api/tick", {}).then(applyState);
    }, 500);
  }

  bindControls();
  applyState(currentState);
  startPolling();
})();
