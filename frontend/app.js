"use strict";

// 相对当前源(客服后端)即可，前端与后端同源挂载在 /ui，接口在根路径 /api/*
const API = {
  chat: "/api/chat",
  chatStream: "/api/chat/stream",
  history: "/api/chat/history",
  orders: "/api/orders",
  reset: "/api/chat/reset",
};

const TYPE_LABEL = {
  order: "订单", hotel: "酒店", scenic_spot: "景点",
  flight: "航班", train: "火车", bus: "汽车",
};
const ORDER_TYPE_LABEL = {
  hotel_room: "酒店", scenic_ticket: "景点", flight_cabin: "机票",
  train_seat: "火车票", bus_seat: "汽车票", transfer_service: "接送",
};
const ORDER_STATUS_LABEL = {
  pending_payment: "待支付", paid: "已支付", in_progress: "进行中",
  finished: "已结束", cancelled: "已取消",
};

const els = {};
const state = {
  senderId: "13",
  streaming: true,
  busy: false,
};

document.addEventListener("DOMContentLoaded", () => {
  cacheEls();
  restoreSettings();
  bindEvents();
  loadHistory();
  loadOrders();
});

function cacheEls() {
  els.messages = document.getElementById("messages");
  els.statusbar = document.getElementById("statusbar");
  els.input = document.getElementById("input");
  els.composer = document.getElementById("composer");
  els.senderId = document.getElementById("senderId");
  els.applyUser = document.getElementById("applyUser");
  els.newSession = document.getElementById("newSession");
  els.streamToggle = document.getElementById("streamToggle");
  els.orderList = document.getElementById("orderList");
  els.refreshOrders = document.getElementById("refreshOrders");
}

function restoreSettings() {
  const saved = localStorage.getItem("senderId");
  if (saved) state.senderId = saved;
  els.senderId.value = state.senderId;
}

function bindEvents() {
  els.composer.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = els.input.value.trim();
    if (!text || state.busy) return;
    els.input.value = "";
    sendText(text);
  });
  els.applyUser.addEventListener("click", applyUserFromInput);
  els.newSession.addEventListener("click", newSession);
  els.streamToggle.addEventListener("change", () => {
    state.streaming = els.streamToggle.checked;
  });
  els.refreshOrders.addEventListener("click", loadOrders);
}

function applyUserFromInput() {
  const v = els.senderId.value.trim();
  if (!v) return;
  state.senderId = v;
  localStorage.setItem("senderId", v);
  loadHistory();
  loadOrders();
}

async function newSession() {
  if (state.busy) return;
  try {
    await fetch(`${API.reset}?sender_id=${encodeURIComponent(state.senderId)}`, { method: "POST" });
  } catch (_) {
    /* 重置失败也继续清前端视图 */
  }
  els.messages.innerHTML = "";
  hideStatus();
  addMessage("bot", "已开始新会话,之前卡住的流程已清空。请问需要什么帮助?", null);
}

// ── 渲染 ──────────────────────────────────────────────

function addMessage(role, text, obj) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + role;

  const label = document.createElement("div");
  label.className = "role";
  label.textContent = role === "user" ? "我" : "客服";
  wrap.appendChild(label);

  let bubble = null;
  if (text !== "" && text != null) {
    bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text; // textContent 防 XSS，CSS white-space:pre-wrap 保留换行
    wrap.appendChild(bubble);
  }

  if (obj) wrap.appendChild(renderCard(obj));

  els.messages.appendChild(wrap);
  els.messages.scrollTop = els.messages.scrollHeight;
  return bubble;
}

function renderCard(obj) {
  const card = document.createElement("div");
  card.className = "card";
  const t = document.createElement("div");
  t.className = "card-type";
  t.textContent = "📎 " + (TYPE_LABEL[obj.type] || obj.type || "业务对象");
  const title = document.createElement("div");
  title.className = "card-title";
  title.textContent = obj.title || obj.id || "";
  card.appendChild(t);
  card.appendChild(title);
  const attrs = obj.attributes || {};
  const keys = Object.keys(attrs);
  if (keys.length) {
    const meta = document.createElement("div");
    meta.className = "card-meta";
    meta.textContent = keys.map((k) => `${k}: ${attrs[k]}`).join("  ·  ");
    card.appendChild(meta);
  }
  return card;
}

function showStatus(text) {
  els.statusbar.hidden = false;
  els.statusbar.textContent = text;
}
function hideStatus() {
  els.statusbar.hidden = true;
  els.statusbar.textContent = "";
}

// ── 发送消息 ──────────────────────────────────────────

async function sendText(text) {
  addMessage("user", text);
  await runChat({ sender_id: state.senderId, text });
}

async function sendOrderCard(order) {
  const obj = {
    id: String(order.orderId),
    type: "order",
    title: order.orderNo || String(order.orderId),
    attributes: {
      类型: ORDER_TYPE_LABEL[order.orderTypeCode] || order.orderTypeCode || "",
      状态: ORDER_STATUS_LABEL[order.statusCode] || order.statusCode || "",
      金额: order.payableAmount != null ? "¥" + order.payableAmount : "",
    },
  };
  addMessage("user", null, obj);
  await runChat({ sender_id: state.senderId, object: obj });
}

async function runChat(payload) {
  setBusy(true);
  try {
    if (state.streaming) await streamChat(payload);
    else await normalChat(payload);
  } catch (err) {
    addMessage("bot", "请求失败：" + (err && err.message ? err.message : err), null)
      .classList.add("error");
  } finally {
    setBusy(false);
    hideStatus();
  }
}

function setBusy(v) {
  state.busy = v;
  els.input.disabled = v;
}

async function normalChat(payload) {
  showStatus("正在处理...");
  const res = await fetch(API.chat, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("HTTP " + res.status);
  const data = await res.json();
  for (const m of data.messages || []) addMessage("bot", m.text, m.object);
}

async function streamChat(payload) {
  const res = await fetch(API.chatStream, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok || !res.body) throw new Error("HTTP " + res.status);

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let botBubble = null; // 当前流式 bot 气泡
  let streamed = "";

  const ensureBubble = () => {
    if (!botBubble) {
      const wrap = document.createElement("div");
      wrap.className = "msg bot";
      const label = document.createElement("div");
      label.className = "role";
      label.textContent = "客服";
      const bubble = document.createElement("div");
      bubble.className = "bubble streaming";
      wrap.appendChild(label);
      wrap.appendChild(bubble);
      els.messages.appendChild(wrap);
      els.messages.scrollTop = els.messages.scrollHeight;
      botBubble = bubble;
    }
    return botBubble;
  };
  const finalizeBubble = (text, obj) => {
    const b = ensureBubble();
    b.textContent = text;
    b.classList.remove("streaming");
    if (obj) b.parentElement.appendChild(renderCard(obj));
    botBubble = null;
    streamed = "";
    els.messages.scrollTop = els.messages.scrollHeight;
  };

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE 以空行分帧
    let sep;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      for (const line of frame.split("\n")) {
        if (!line.startsWith("data:")) continue;
        const jsonStr = line.slice(5).trim();
        if (!jsonStr) continue;
        let evt;
        try { evt = JSON.parse(jsonStr); } catch (_) { continue; }
        handleEvent(evt);
      }
    }
  }

  function handleEvent(evt) {
    const d = evt.data || {};
    switch (evt.type) {
      case "stage":
      case "progress":
        showStatus(d.text || "");
        break;
      case "delta":
        streamed += d.token || "";
        ensureBubble().textContent = streamed;
        els.messages.scrollTop = els.messages.scrollHeight;
        break;
      case "message":
        // 最终完整文本，权威替换逐字流
        finalizeBubble(d.text || "", d.object || null);
        break;
      case "error":
        addMessage("bot", d.text || "处理出错", null).classList.add("error");
        break;
      case "done":
        break;
      default:
        break;
    }
  }
}

// ── 历史 & 订单 ───────────────────────────────────────

async function loadHistory() {
  try {
    const res = await fetch(`${API.history}?sender_id=${encodeURIComponent(state.senderId)}`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    els.messages.innerHTML = "";
    const msgs = data.messages || [];
    if (!msgs.length) {
      addMessage("bot", "你好！我是旅游小助手 🧭 可以帮你查酒店、景点、机票火车票，查订单、办退款，或转人工。", null);
      return;
    }
    for (const m of msgs) addMessage(m.role, m.text, m.object);
    els.messages.scrollTop = els.messages.scrollHeight;
  } catch (err) {
    addMessage("bot", "加载历史失败：" + err.message, null).classList.add("error");
  }
}

async function loadOrders() {
  els.orderList.innerHTML = '<li class="empty">加载中...</li>';
  try {
    const res = await fetch(`${API.orders}?sender_id=${encodeURIComponent(state.senderId)}&pageSize=20`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    renderOrders(data.orders || []);
  } catch (err) {
    els.orderList.innerHTML = `<li class="empty">加载订单失败<br/>${err.message}</li>`;
  }
}

function renderOrders(orders) {
  els.orderList.innerHTML = "";
  if (!orders.length) {
    els.orderList.innerHTML = '<li class="empty">该用户暂无订单</li>';
    return;
  }
  for (const o of orders) {
    const li = document.createElement("li");
    li.className = "order-item";

    const top = document.createElement("div");
    top.className = "oi-top";
    const no = document.createElement("span");
    no.className = "oi-no";
    no.textContent = o.orderNo || ("#" + o.orderId);
    const st = document.createElement("span");
    st.className = "oi-status" + (o.statusCode === "paid" ? " paid" : "");
    st.textContent = ORDER_STATUS_LABEL[o.statusCode] || o.statusCode || "";
    top.appendChild(no); top.appendChild(st);

    const meta = document.createElement("div");
    meta.className = "oi-meta";
    const amt = o.payableAmount != null ? " ¥" + o.payableAmount : "";
    meta.textContent = (ORDER_TYPE_LABEL[o.orderTypeCode] || o.orderTypeCode || "") + amt;

    const btn = document.createElement("button");
    btn.className = "btn ghost sm";
    btn.textContent = "发送卡片";
    btn.addEventListener("click", () => {
      if (state.busy) return;
      sendOrderCard(o);
    });

    li.appendChild(top); li.appendChild(meta); li.appendChild(btn);
    els.orderList.appendChild(li);
  }
}
