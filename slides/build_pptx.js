// Build FUWA_FUWA_e-Shop.pptx  —  run: NODE_PATH=<dir with pptxgenjs> node build_pptx.js
const pptxgen = require("pptxgenjs");
const path = require("path");
const IMG = (f) => path.join(__dirname, "img", f);

const ZH = "Microsoft JhengHei";
const EN = "Arial Rounded MT Bold";
const EN2 = "Calibri";

const K = { // palette (same as the website)
  cream: "FBEFB8", cream2: "FFF5E6", sand: "FCDF8C", peach: "FFE4B5",
  orange: "E88D67", orange2: "F6BB6F", red: "D56B59", brick: "B05848",
  brown: "5D4037", white: "FFFFFF", mute: "8A6A5D", green: "E8F1D9", greenD: "6F9446",
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "FUWA FUWA e-Shop";
pres.author = "Frank";

// ---------- layouts ----------
function awning() {
  const objs = [];
  const n = 12, w = 13.333 / n;
  for (let i = 0; i < n; i++) {
    objs.push({ rect: { x: i * w, y: -0.4, w: w + 0.01, h: 1.05, fill: { color: i % 2 ? K.red : K.orange2 }, rectRadius: 0.27 } });
  }
  return objs;
}
pres.defineSlideMaster({
  title: "BASE", background: { color: K.cream },
  objects: [...awning(),
    { text: { text: "FUWA FUWA e-Shop", options: { x: 0.6, y: 7.05, w: 5, h: 0.3, fontFace: EN2, fontSize: 11, color: "A07D6C", margin: 0 } } }],
  slideNumber: { x: 11.9, y: 7.05, w: 0.85, h: 0.3, fontFace: EN2, fontSize: 11, color: "A07D6C", align: "right", margin: 0 },
});
pres.defineSlideMaster({
  title: "HILLS", background: { color: K.cream },
  objects: [{ image: { path: IMG("hills.png"), x: 0, y: 5.9, w: 13.333, h: 1.6 } }, ...awning()],
  slideNumber: { x: 11.9, y: 7.05, w: 0.85, h: 0.3, fontFace: EN2, fontSize: 11, color: "A07D6C", align: "right", margin: 0 },
});

// ---------- helpers ----------
let shadowFn = () => ({ type: "outer", color: "5D4037", opacity: 0.18, blur: 0, offset: 3, angle: 90 });
function card(s, x, y, w, h, o = {}) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: o.r ?? 0.2,
    fill: { color: o.fill || K.white }, line: { color: o.line || K.orange2, width: 2 },
    shadow: o.noShadow ? undefined : shadowFn(),
  });
}
function txt(s, text, x, y, w, h, o = {}) {
  s.addText(text, Object.assign({ x, y, w, h, margin: 0, fontFace: ZH, fontSize: 14, color: K.brown, valign: "top", isTextBox: true }, o));
}
function pill(s, text, x, y, w, h, o = {}) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: h / 2, fill: { color: o.fill || K.red }, line: { color: o.line || o.fill || K.red, width: 1.5 } });
  txt(s, text, x, y, w, h, { align: "center", valign: "middle", fontFace: o.font || EN, fontSize: o.size || 12, color: o.color || K.white, bold: !!o.bold });
}
function circle(s, text, x, y, d, o = {}) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: o.fill || K.red }, line: { color: o.fill || K.red, width: 1 } });
  txt(s, text, x, y, d, d, { align: "center", valign: "middle", fontFace: EN, fontSize: o.size || 14, color: o.color || K.white });
}
function header(s, kicker, zh, en) {
  txt(s, kicker, 0.6, 0.82, 9, 0.28, { fontFace: EN, fontSize: 12, color: K.red, charSpacing: 2 });
  txt(s, zh, 0.6, 1.08, 12, 0.6, { fontSize: 30, bold: true, color: K.brick, valign: "middle" });
  txt(s, en, 0.6, 1.66, 12, 0.36, { fontFace: EN, fontSize: 16, color: K.orange, valign: "middle" });
}
function bi(zh, en, zhSize, enSize, o = {}) { // two-paragraph run list: zh + en
  return [
    { text: zh, options: Object.assign({ fontFace: ZH, fontSize: zhSize, bold: !!o.bold, color: o.zhColor || K.brown, breakLine: true }, o.zhOpts || {}) },
    { text: en, options: { fontFace: EN2, fontSize: enSize, color: o.enColor || K.mute } },
  ];
}
const notes = (s, t) => s.addNotes(t);

// =====================================================================
// 1  TITLE
// =====================================================================
{
  const s = pres.addSlide({ masterName: "HILLS" });
  s.addImage({ path: IMG("fuwa_title.png"), x: 0.9, y: 2.0, w: 5.9, h: 0.65, altText: "FUWA FUWA logo" });
  txt(s, "資料庫系統 期末專題簡報", 0.9, 2.95, 7, 0.75, { fontSize: 38, bold: true, color: K.brick, valign: "middle" });
  txt(s, "Database Systems · Final Project", 0.9, 3.7, 7, 0.45, { fontFace: EN, fontSize: 22, color: K.orange, valign: "middle" });
  pill(s, "e-Shop 電子商店系統", 0.9, 4.4, 2.6, 0.5, { fill: K.peach, line: K.orange2, color: K.brown, font: ZH, size: 14, bold: true });
  pill(s, "Phase 1 · 2   SRS → ER → Schema", 3.65, 4.4, 3.7, 0.5, { fill: K.peach, line: K.orange2, color: K.brown, size: 14 });
  s.addImage({ path: IMG("All.png"), x: 8.1, y: 1.15, w: 4.6, h: 4.54, altText: "FUWA FUWA mascot" });
  s.addImage({ path: IMG("dog.png"), x: 0.9, y: 5.55, w: 0.62, h: 0.72, altText: "dog" });
  txt(s, "NTUT · 115-1 · 資料庫系統  Database Systems", 3.2, 7.05, 6, 0.3, { fontSize: 11, color: "A07D6C", fontFace: ZH, align: "center" });
  notes(s, "(約 20 秒) 大家好，我們的專題是 FUWA FUWA e-Shop，一個多商店的線上購物系統。今天依序介紹：使用者故事、系統架構、ER 模型、Schema，以及我們怎麼用 AI 幫忙把需求想清楚。");
}

// =====================================================================
// 2  OVERVIEW
// =====================================================================
{
  const s = pres.addSlide({ masterName: "BASE" });
  header(s, "PROJECT OVERVIEW · 專案概觀", "一個多商店的線上購物系統", "A multi-store online shopping system");
  s.addImage({ path: IMG("dog.png"), x: 12.0, y: 0.78, w: 0.72, h: 0.84, altText: "dog" });
  const stats = [["3", "使用者角色", "User roles"], ["8", "子系統", "Subsystems"], ["26", "商業規則", "Business rules"], ["15", "資料表", "Database tables"]];
  const cw = 2.84, gap = 0.257;
  stats.forEach((st, i) => {
    const x = 0.6 + i * (cw + gap);
    card(s, x, 2.2, cw, 0.95);
    txt(s, st[0], x + 0.2, 2.2, 0.95, 0.95, { fontFace: EN, fontSize: 36, color: K.red, valign: "middle" });
    s.addText(bi(st[1], st[2], 15, 11, { bold: true }), { x: x + 1.15, y: 2.2, w: cw - 1.25, h: 0.95, margin: 0, valign: "middle", isTextBox: true });
  });
  const subs = [
    ["AAS", "帳號與權限", "Accounts & Auth", "登入、註冊、角色授權"],
    ["PMS", "商品管理", "Products", "搜尋、新增、修改、庫存"],
    ["SCS", "購物車", "Shopping Cart", "加入、調整數量、移除"],
    ["OMS", "訂單管理", "Orders", "結帳、狀態、取消、退貨"],
    ["DMS", "折扣管理", "Discounts", "運費／季節／特殊活動"],
    ["RSS", "報表統計", "Reports", "日、週、月銷售報表"],
    ["STS", "商店管理", "Stores", "商店資料與評價"],
    ["DBS", "資料庫", "Database", "儲存與完整性限制"],
  ];
  subs.forEach((b, i) => {
    const x = 0.6 + (i % 4) * (cw + gap), y = 3.45 + Math.floor(i / 4) * 1.7;
    const last = i === 7;
    card(s, x, y, cw, 1.5, last ? { fill: K.green, line: "9DBB74" } : {});
    txt(s, b[0], x, y + 0.1, cw, 0.35, { fontFace: EN, fontSize: 18, color: last ? K.greenD : K.red, align: "center", valign: "middle", charSpacing: 1 });
    txt(s, b[1], x, y + 0.46, cw, 0.32, { fontSize: 16, bold: true, align: "center", valign: "middle" });
    txt(s, b[2], x, y + 0.78, cw, 0.25, { fontFace: EN2, fontSize: 12, color: K.mute, align: "center", valign: "middle" });
    txt(s, b[3], x, y + 1.06, cw, 0.3, { fontSize: 13, align: "center", valign: "middle", color: "6B4F44" });
  });
  notes(s, "(約 40 秒) 系統有顧客、工作人員、系統管理員三種角色，切成 8 個子系統，整理出 26 條商業規則，最後落成 15 張資料表。");
}

// =====================================================================
// 3  USER STORIES
// =====================================================================
{
  const s = pres.addSlide({ masterName: "BASE" });
  header(s, "USER STORIES · 使用者故事", "19 則故事，三種角色", "19 user stories across three roles");
  s.addImage({ path: IMG("hat.png"), x: 11.7, y: 0.85, w: 1.0, h: 0.71, altText: "hat" });
  const cols = [
    { zh: "顧客 / 訪客", en: "Customer / Guest", img: "dog.png", ar: 0.86, st: [
      ["US-01", "搜尋商品", "Search products by keyword"], ["US-04", "管理購物車", "Add, edit and remove cart items"],
      ["US-05", "看見完整金額明細", "See the full price breakdown"], ["US-09", "取消未處理訂單", "Cancel a “received” order"],
      ["US-10", "申請退貨", "Request a full or partial return"]] },
    { zh: "工作人員", en: "Staff", img: "brush.png", ar: 0.99, st: [
      ["US-12", "管理商品與庫存", "Manage products and stock"], ["US-13", "依序更新訂單狀態", "Advance order status in order"],
      ["US-14", "審核退貨申請", "Approve or reject returns"], ["US-15", "設定三種折扣", "Create three kinds of discounts"],
      ["US-17", "查看銷售報表", "Daily, weekly, monthly reports"]] },
    { zh: "系統管理員", en: "Administrator", img: "collar.png", ar: 1.0, st: [["US-19", "管理使用者帳號", "Manage and deactivate accounts"]] },
  ];
  const cw = 3.88, gap = 0.255;
  cols.forEach((c, i) => {
    const x = 0.6 + i * (cw + gap), y = 2.2, h = 4.65;
    card(s, x, y, cw, h);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.2, y: y + 0.18, w: 0.66, h: 0.66, fill: { color: K.peach }, line: { color: K.orange2, width: 2 } });
    const ih = 0.46, iw = ih * (c.ar === 0.99 ? 1.0 : c.ar);
    s.addImage({ path: IMG(c.img), x: x + 0.53 - iw / 2, y: y + 0.51 - ih / 2, w: iw, h: ih, altText: c.en });
    s.addText(bi(c.zh, c.en, 18, 12, { bold: true, enColor: K.orange }), { x: x + 1.05, y: y + 0.15, w: cw - 1.2, h: 0.72, margin: 0, valign: "middle", isTextBox: true });
    c.st.forEach((r, k) => {
      const ry = y + 1.05 + k * 0.7;
      if (k) s.addShape(pres.ShapeType.line, { x: x + 0.2, y: ry - 0.06, w: cw - 0.4, h: 0, line: { color: "F2CFA0", width: 1.25, dashType: "dash" } });
      pill(s, r[0], x + 0.2, ry + 0.06, 0.72, 0.28, { fill: K.orange, size: 10 });
      s.addText(bi(r[1], r[2], 14, 11, { bold: true }), { x: x + 1.05, y: ry, w: cw - 1.2, h: 0.6, margin: 0, valign: "top", isTextBox: true });
    });
    if (i === 2) {
      const bx = x + 0.2, bw = cw - 0.4;
      s.addShape(pres.ShapeType.roundRect, { x: bx, y: y + 1.9, w: bw, h: 1.3, rectRadius: 0.14, fill: { color: K.cream2 }, line: { color: K.cream2 } });
      s.addText([
        { text: "一個人可以有多個角色", options: { fontFace: ZH, fontSize: 14, bold: true, breakLine: true } },
        { text: "A user may hold several roles", options: { fontFace: EN2, fontSize: 11, color: K.mute, breakLine: true } },
        { text: "管理員可兼任工作人員 → ER 以多值屬性 role 表示", options: { fontFace: ZH, fontSize: 12 } },
      ], { x: bx + 0.12, y: y + 1.98, w: bw - 0.24, h: 1.14, margin: 0, isTextBox: true, valign: "top" });
      s.addShape(pres.ShapeType.roundRect, { x: bx, y: y + 3.32, w: bw, h: 1.15, rectRadius: 0.14, fill: { color: K.cream2 }, line: { color: K.cream2 } });
      s.addText([
        { text: "選配故事 Optional", options: { fontFace: ZH, fontSize: 14, bold: true, breakLine: true } },
        { text: "訪客註冊、訂單確認信、商店評價、暢銷統計 (US-02 / 07 / 11 / 18)", options: { fontFace: ZH, fontSize: 12 } },
      ], { x: bx + 0.12, y: y + 3.4, w: bw - 0.24, h: 1.0, margin: 0, isTextBox: true, valign: "top" });
    }
  });
  txt(s, "Source: Phase 1 SRS §2.2", 9.0, 7.05, 2.8, 0.3, { fontFace: EN2, fontSize: 11, color: "A07D6C", align: "right" });
  notes(s, "(約 55 秒) 顧客重點是搜尋、購物車、看到完整金額、取消與退貨；工作人員管理商品、訂單、退貨與折扣；管理員管帳號。一個人可以有多個角色，所以 ER 圖用多值屬性 role。");
}

// =====================================================================
// 4  ARCHITECTURE
// =====================================================================
{
  const s = pres.addSlide({ masterName: "BASE" });
  header(s, "SYSTEM ARCHITECTURE · 系統架構圖", "瀏覽器 → REST API → PostgreSQL", "Browser → REST API → PostgreSQL");
  const X = 0.6, W = 9.2;
  const arrow = (y, h, label) => {
    s.addShape(pres.ShapeType.line, { x: X + W / 2, y, w: 0, h, line: { color: K.brick, width: 2.5, beginArrowType: label ? "triangle" : undefined, endArrowType: "triangle" } });
    if (label) txt(s, label, X + W / 2 + 0.2, y, 3, h, { fontFace: EN2, fontSize: 11, color: K.brick, valign: "middle", bold: true });
  };
  // users
  s.addShape(pres.ShapeType.roundRect, { x: X, y: 2.1, w: W, h: 0.62, rectRadius: 0.18, fill: { color: K.white }, line: { color: K.orange2, width: 2 } });
  [["顧客", "Customer"], ["工作人員", "Staff"], ["系統管理員", "Admin"]].forEach((a, i) => {
    const cx = X + W / 6 + i * (W / 3);
    s.addShape(pres.ShapeType.ellipse, { x: cx - 1.1, y: 2.2, w: 0.42, h: 0.42, fill: { color: K.peach }, line: { color: K.orange2, width: 2 } });
    s.addText(bi(a[0], a[1], 14, 10, { bold: true }), { x: cx - 0.6, y: 2.14, w: 1.8, h: 0.54, margin: 0, valign: "middle", isTextBox: true });
  });
  arrow(2.74, 0.2);
  // front end
  s.addShape(pres.ShapeType.roundRect, { x: X, y: 2.96, w: W, h: 1.02, rectRadius: 0.18, fill: { color: "FFF1C9" }, line: { color: K.orange2, width: 2 } });
  pill(s, "Browser · 前端 Frontend", X + 0.2, 2.86, 2.6, 0.26, { fill: K.orange, size: 11 });
  [["顧客前台", "Storefront", 0.2, 3.5], ["工作人員／管理員後台", "Staff & Admin console", 3.9, 5.1]].forEach((b) => {
    s.addShape(pres.ShapeType.roundRect, { x: X + b[2], y: 3.22, w: b[3], h: 0.5, rectRadius: 0.1, fill: { color: K.white }, line: { color: K.orange2, width: 1.5 } });
    s.addText(bi(b[0], b[1], 13, 10, { bold: true }), { x: X + b[2], y: 3.22, w: b[3], h: 0.5, margin: 0, align: "center", valign: "middle", isTextBox: true });
  });
  txt(s, "React 18 + TypeScript + Vite (SPA)", X, 3.74, W, 0.2, { fontFace: EN2, fontSize: 10, color: K.mute, align: "center" });
  arrow(3.99, 0.3, "HTTP(S) · REST / JSON");
  // back end
  s.addShape(pres.ShapeType.roundRect, { x: X, y: 4.31, w: W, h: 1.72, rectRadius: 0.18, fill: { color: "FFE6DA" }, line: { color: K.orange, width: 2 } });
  pill(s, "FastAPI · 後端 Backend", X + 0.2, 4.2, 2.5, 0.26, { fill: K.red, size: 11 });
  const subs = [["AAS", "帳號權限"], ["PMS", "商品"], ["SCS", "購物車"], ["OMS", "訂單"], ["DMS", "折扣"], ["RSS", "報表"], ["STS", "商店"]];
  const bw = 1.17, bg = (W - 0.4 - 7 * bw) / 6;
  subs.forEach((b, i) => {
    const bx = X + 0.2 + i * (bw + bg);
    s.addShape(pres.ShapeType.roundRect, { x: bx, y: 4.58, w: bw, h: 0.6, rectRadius: 0.1, fill: { color: K.white }, line: { color: K.orange2, width: 1.5 } });
    s.addText([{ text: b[0], options: { fontFace: EN, fontSize: 12, color: K.red, breakLine: true } }, { text: b[1], options: { fontFace: ZH, fontSize: 11 } }], { x: bx, y: 4.58, w: bw, h: 0.6, margin: 0, align: "center", valign: "middle", isTextBox: true });
  });
  [["JWT 驗證 · 角色授權 · bcrypt", "Auth · RBAC · password hashing", 0.2, 4.45], ["SQLAlchemy", "ORM / SQL", 4.8, 4.2]].forEach((b) => {
    s.addShape(pres.ShapeType.roundRect, { x: X + b[2], y: 5.3, w: b[3], h: 0.6, rectRadius: 0.1, fill: { color: K.white }, line: { color: K.orange2, width: 1.5 } });
    s.addText(bi(b[0], b[1], 13, 10, { bold: true }), { x: X + b[2], y: 5.3, w: b[3], h: 0.6, margin: 0, align: "center", valign: "middle", isTextBox: true });
  });
  arrow(6.04, 0.26, "SQL");
  // db + smtp
  s.addShape(pres.ShapeType.roundRect, { x: X, y: 6.32, w: 5.0, h: 0.62, rectRadius: 0.18, fill: { color: K.green }, line: { color: "9DBB74", width: 2 } });
  s.addText(bi("DBS · PostgreSQL 16", "15 tables · constraints · triggers", 14, 10, { bold: true }), { x: X, y: 6.32, w: 5.0, h: 0.62, margin: 0, align: "center", valign: "middle", isTextBox: true });
  s.addShape(pres.ShapeType.roundRect, { x: X + 5.2, y: 6.32, w: 4.0, h: 0.62, rectRadius: 0.18, fill: { color: K.white }, line: { color: K.orange2, width: 2, dashType: "dash" } });
  s.addText(bi("SMTP 郵件伺服器（選配）", "Order confirmation email · optional", 13, 10, { bold: true }), { x: X + 5.2, y: 6.32, w: 4.0, h: 0.62, margin: 0, align: "center", valign: "middle", isTextBox: true });
  // side panel
  const SX = 10.05, SW = 2.68;
  card(s, SX, 2.1, SW, 3.35);
  txt(s, "WHY THIS STACK", SX + 0.18, 2.2, SW - 0.3, 0.26, { fontFace: EN, fontSize: 11, color: K.red, charSpacing: 1 });
  txt(s, "為什麼這樣選", SX + 0.18, 2.45, SW - 0.3, 0.26, { fontSize: 13, bold: true });
  [["沿用前端、重構後端", "Re-use the UI, rebuild the backend"], ["權限在後端把關 (BR-21)", "RBAC enforced on the server"], ["完整性交給資料庫", "CHECK · FK · EXCLUDE"]].forEach((p, i) => {
    s.addText(bi(p[0], p[1], 12, 10, { bold: true }), { x: SX + 0.18, y: 2.8 + i * 0.86, w: SW - 0.32, h: 0.76, margin: 0, valign: "top", isTextBox: true });
  });
  card(s, SX, 5.6, SW, 1.34, { fill: K.peach });
  s.addImage({ path: IMG("dog_product_illustration.png"), x: SX + 0.75, y: 5.66, w: 1.18, h: 1.08, altText: "dog with a can" });
  txt(s, "Source: Phase 2 SRS · Figure 1", 9.0, 7.05, 2.8, 0.3, { fontFace: EN2, fontSize: 11, color: "A07D6C", align: "right" });
  notes(s, "(約 55 秒) 使用者用瀏覽器開 React 前端，前端用 REST/JSON 呼叫 FastAPI 後端。後端依功能分成 7 個子系統，負責 JWT 驗證與角色授權，再透過 SQLAlchemy 存取 PostgreSQL。訂單確認信是選配，用虛線表示。權限在後端把關，資料完整性則交給資料庫。");
}

// =====================================================================
// 5  ER
// =====================================================================
function diagramSlide(kicker, zh, en, imgFile, imgAr, pts, src, noteText, badge) {
  const s = pres.addSlide({ masterName: "BASE" });
  header(s, kicker, zh, en);
  const cx = 0.6, cy = 2.1, cw = 7.6, ch = 4.85;
  card(s, cx, cy, cw, ch);
  let iw = cw - 0.3, ih = iw / imgAr;
  if (ih > ch - 0.3) { ih = ch - 0.3; iw = ih * imgAr; }
  s.addImage({ path: IMG(imgFile), x: cx + (cw - iw) / 2, y: cy + (ch - ih) / 2, w: iw, h: ih, altText: en });
  const px = 8.45, pw = 4.28;
  let y = cy;
  if (badge) {
    const bw = (pw - 0.3) / 3;
    badge.forEach((b, i) => {
      const bx = px + i * (bw + 0.15);
      s.addShape(pres.ShapeType.roundRect, { x: bx, y, w: bw, h: 0.9, rectRadius: 0.16, fill: { color: [K.red, K.orange, K.orange2][i] }, line: { color: [K.red, K.orange, K.orange2][i] }, shadow: shadowFn() });
      s.addText([{ text: b[0], options: { fontFace: EN, fontSize: 26, breakLine: true } }, { text: b[1], options: { fontFace: ZH, fontSize: 11, bold: true } }], { x: bx, y, w: bw, h: 0.9, margin: 0, align: "center", valign: "middle", color: i === 2 ? K.brown : K.white, isTextBox: true });
    });
    y += 0.97;
  }
  const ph = (cy + ch - y - 0.12 * (pts.length - 1)) / pts.length;
  pts.forEach((p, i) => {
    const py = y + i * (ph + 0.12);
    card(s, px, py, pw, ph, { r: 0.16 });
    circle(s, p[0], px + 0.15, py + 0.14, 0.44, { size: p[0].length > 1 ? 11 : 15 });
    s.addText([
      { text: p[1], options: { fontFace: ZH, fontSize: 14, bold: true, breakLine: true } },
      { text: p[2], options: { fontFace: ZH, fontSize: 12, color: "6B4F44", breakLine: true } },
      { text: p[3], options: { fontFace: EN2, fontSize: 10.5, color: K.mute } },
    ], { x: px + 0.72, y: py + 0.06, w: pw - 0.85, h: ph - 0.1, margin: 0, valign: "top", isTextBox: true });
  });
  txt(s, src, 7.2, 7.05, 4.6, 0.3, { fontFace: EN2, fontSize: 11, color: "A07D6C", align: "right" });
  notes(s, noteText);
  return s;
}
diagramSlide("ER MODEL · 實體關係模型", "9 個實體、13 個關係", "9 entities · 13 relationships", "er.png", 3636 / 2618,
  [["1", "商品 1 : N 商店", "每個商品屬於一間商店，一筆訂單可含不同商店的商品", "One store → many products; an order may span stores"],
   ["2", "ORDER_ITEM 是弱實體", "保存下單當下的品名與單價，退貨也指向某一項明細", "Snapshot of name & price; returns point to a line item"],
   ["3", "角色用多值屬性", "管理員可兼任工作人員，不用拆成三個子類別", "Multi-valued role instead of three subclasses"]],
  "Source: Phase 2 SRS §3 · ER.drawio",
  "(約 55 秒) 我們有 9 個實體、13 個關係，其中 ORDER_ITEM 與 STATUS_HISTORY 是弱實體。重點三個：一個商品屬於一間商店但訂單可跨店；訂單明細保存下單當下的品名與單價；角色用多值屬性。(圖太小可以在網頁版簡報點圖放大)",
  [["9", "實體\nEntities"], ["13", "關係\nRelationships"], ["2", "弱實體\nWeak"]]);

// =====================================================================
// 6  SCHEMA
// =====================================================================
diagramSlide("RELATIONAL SCHEMA · 關聯綱要", "15 張資料表，規則寫進資料庫", "15 tables, with the rules enforced inside the database", "schema.png", 2235 / 1243,
  [["PK", "複合主鍵處理 M:N 與弱實體", "cart_item (user, product)、order_item (order, item_no)", "Composite keys for M:N and weak entities"],
   ["CK", "CHECK 限制取值範圍", "價格 > 0、庫存 ≥ 0、狀態只有 6 種、折扣率 0~1", "Value rules: price, stock, status, rate"],
   ["FK", "複合外鍵守住折扣期間", "product_discount 以複合 FK 對應 discount，期間一致", "Composite FK keeps discount periods consistent"],
   ["EX", "EXCLUDE 防止期間重疊 (BR-13)", "同一商品的特殊活動折扣，日期區間不能重疊", "EXCLUDE USING gist — no overlapping periods"]],
  "Source: Phase 2 · schema.sql (PostgreSQL 16+)",
  "(約 55 秒) ER 轉成 15 張表。複合主鍵處理多對多與弱實體；CHECK 限制價格、庫存、狀態與折扣率；複合外鍵讓折扣期間一致；最特別的是 EXCLUDE 約束，讓同一商品的特殊活動折扣期間不可能重疊 (BR-13)，這條規則由資料庫本身保證。");

// =====================================================================
// 7  HOW WE USE AI
// =====================================================================
{
  const s = pres.addSlide({ masterName: "BASE" });
  header(s, "HOW WE USE AI · 我們怎麼用 AI", "用 AI 找出「還沒想清楚」的地方", "Using AI to surface what we hadn’t thought through");
  s.addImage({ path: IMG("All.png"), x: 11.75, y: 0.78, w: 1.0, h: 0.99, altText: "mascot" });
  const steps = [["我們先提出構想", "We draft the idea"], ["AI 反問模糊之處", "AI asks what’s unclear"], ["我們討論並決定", "We discuss & decide"], ["寫進商業規則", "Recorded as business rules"]];
  const sw = 2.78, sg = 0.337;
  steps.forEach((st, i) => {
    const x = 0.6 + i * (sw + sg);
    card(s, x, 2.1, sw, 0.62, { r: 0.18 });
    s.addText(bi(st[0], st[1], 13, 10, { bold: true }), { x, y: 2.1, w: sw, h: 0.62, margin: 0, align: "center", valign: "middle", isTextBox: true });
    if (i < 3) txt(s, "→", x + sw, 2.1, sg, 0.62, { fontFace: EN, fontSize: 20, color: K.red, align: "center", valign: "middle" });
  });
  const dec = [
    ["BR-03", "商品與商店的關係？一筆訂單能同時買不同商店的商品嗎？", "Product–store relationship? Can an order span stores?", "一商品一商店，訂單可跨店", "One store per product; orders may span stores"],
    ["BR-15", "折扣率怎麼表示？題目寫 0.05%，我們假設是筆誤、實際指 5%", "“0.05%” looks like a typo — we assume 5%", "小數 0~1，0.05 = 折 5%", "Decimal in (0,1): 0.05 = 5% off"],
    ["BR-22", "稅率和基本運費要定多少？", "What tax rate and base shipping fee?", "稅 5%、運費 100 元（系統參數）", "5% tax, NT$100 shipping — stored as settings"],
    ["BR-19 · 25", "要不要讓顧客取消訂單？不同狀態申請退貨怎麼處理？", "Cancellation, and returns at each order status?", "received 自動取消，之後需廠家同意", "Auto-cancel at “received”; later needs store approval"],
    ["BR-10", "訂單金額的計算順序與稅基？", "Calculation order and the tax base?", "先扣折扣，再算稅", "Apply discounts first, then tax"],
    ["BR-12", "多筆折扣同時有效時怎麼套用？", "How do multiple active discounts combine?", "季節性折扣連乘；達任一門檻免運", "Seasonal rates multiply; any threshold waives shipping"],
  ];
  const cw = 3.88, gx = 0.245, ch = 2.0, gy = 0.18;
  dec.forEach((d, i) => {
    const x = 0.6 + (i % 3) * (cw + gx), y = 2.95 + Math.floor(i / 3) * (ch + gy);
    card(s, x, y, cw, ch);
    pill(s, d[0], x + cw - 1.25, y - 0.14, 1.1, 0.28, { fill: K.red, size: 10 });
    s.addText([
      { text: d[1], options: { fontFace: ZH, fontSize: 13, bold: true, breakLine: true } },
      { text: d[2], options: { fontFace: EN2, fontSize: 10.5, color: K.mute } },
    ], { x: x + 0.18, y: y + 0.15, w: cw - 0.36, h: 0.92, margin: 0, valign: "top", isTextBox: true });
    s.addShape(pres.ShapeType.roundRect, { x: x + 0.18, y: y + 1.1, w: cw - 0.36, h: 0.74, rectRadius: 0.1, fill: { color: K.cream2 }, line: { color: K.cream2 } });
    s.addText([
      { text: "✔ " + d[3], options: { fontFace: ZH, fontSize: 13, bold: true, color: K.brown, breakLine: true } },
      { text: d[4], options: { fontFace: EN2, fontSize: 10.5, color: K.mute } },
    ], { x: x + 0.3, y: y + 1.14, w: cw - 0.6, h: 0.66, margin: 0, valign: "middle", isTextBox: true });
  });
  txt(s, "AI asks · humans decide · rules are recorded", 5.2, 7.05, 6.6, 0.3, { fontFace: EN2, fontSize: 11, color: "A07D6C", align: "right" });
  notes(s, "(約 90 秒) 我們先提出構想，再請 AI 反問還沒想清楚的地方，然後由我們討論決定、寫進商業規則。例如：商品與商店的關係、一筆訂單能不能跨店 (BR-03)；題目寫的 0.05% 我們假設是筆誤，實際指 5% (BR-15)；稅 5%、運費 100 元 (BR-22)；顧客可取消與退貨，received 時自動取消，之後需廠家同意 (BR-19/25)；先扣折扣再算稅 (BR-10)；多筆折扣的疊加方式 (BR-12)。AI 負責提問，人負責做決定。");
}

// =====================================================================
// 8  RULES IN ACTION
// =====================================================================
{
  const s = pres.addSlide({ masterName: "BASE" });
  header(s, "DECISIONS → DESIGN · 決定如何變成設計", "金額怎麼算、訂單怎麼走", "How totals are computed and how orders move");
  const steps = [["1", "商品小計", "Subtotal", "單價 × 數量"], ["2", "特殊活動折扣", "Product event discount", "商品層級；買 X 送 Y 或折扣率"], ["3", "季節性折扣", "Seasonal discount", "訂單層級；多筆連乘"], ["4", "稅 5%", "Tax", "以折扣後金額計算，四捨五入"], ["5", "運費 NT$100", "Shipping", "不課稅；折後達門檻免運"]];
  const ops = ["−", "−", "+", "+"];
  const cw = 2.1, og = 0.4325;
  steps.forEach((st, i) => {
    const x = 0.6 + i * (cw + og), y = 2.3;
    card(s, x, y, cw, 1.6);
    circle(s, st[0], x + cw / 2 - 0.17, y - 0.17, 0.34, { size: 12 });
    s.addText([
      { text: st[1], options: { fontFace: ZH, fontSize: 15, bold: true, breakLine: true } },
      { text: st[2], options: { fontFace: EN2, fontSize: 11, color: K.mute, breakLine: true } },
      { text: st[3], options: { fontFace: ZH, fontSize: 12, color: "6B4F44" } },
    ], { x: x + 0.1, y: y + 0.22, w: cw - 0.2, h: 1.3, margin: 0, align: "center", valign: "top", isTextBox: true });
    if (i < 4) txt(s, ops[i], x + cw, y, og, 1.6, { fontFace: EN, fontSize: 24, color: K.red, align: "center", valign: "middle" });
  });
  card(s, 0.6, 4.2, 12.13, 0.85);
  pill(s, "範例 Example", 0.85, 4.45, 1.6, 0.34, { fill: K.orange, size: 12 });
  s.addText([
    { text: "1,000 × 0.95 = ", options: { fontFace: EN, fontSize: 18 } }, { text: "950", options: { fontFace: EN, fontSize: 18, color: K.red } },
    { text: "   →   稅 950 × 5% = ", options: { fontFace: ZH, fontSize: 16 } }, { text: "48", options: { fontFace: EN, fontSize: 18, color: K.red } },
    { text: "   →   950 + 48 + 100 = ", options: { fontFace: EN, fontSize: 18 } }, { text: "1,098", options: { fontFace: EN, fontSize: 18, color: K.red } },
  ], { x: 2.65, y: 4.2, w: 7.9, h: 0.85, margin: 0, valign: "middle", isTextBox: true });
  txt(s, "seasonal 5% · tax rounded · shipping added", 10.4, 4.2, 2.2, 0.85, { fontFace: EN2, fontSize: 10.5, color: K.mute, valign: "middle", align: "right" });
  card(s, 0.6, 5.3, 10.0, 1.65);
  s.addText([
    { text: "訂單狀態  ", options: { fontFace: ZH, fontSize: 15, bold: true } },
    { text: "Order status lifecycle (BR-19, BR-25)", options: { fontFace: EN2, fontSize: 12, color: K.orange } },
  ], { x: 0.85, y: 5.4, w: 9.5, h: 0.32, margin: 0, isTextBox: true, valign: "middle" });
  const chips = [["received", 0.85, K.orange2, K.orange, K.brown], ["processing", 2.55, K.orange2, K.orange, K.brown], ["shipping", 4.25, K.orange2, K.orange, K.brown], ["closed", 5.95, K.orange2, K.orange, K.brown], ["cancelled", 7.7, K.red, K.brick, K.white], ["returned", 9.0, K.red, K.brick, K.white]];
  chips.forEach((c, i) => {
    const w = i < 4 ? 1.35 : 1.2;
    s.addShape(pres.ShapeType.roundRect, { x: c[1], y: 5.82, w, h: 0.42, rectRadius: 0.14, fill: { color: c[2] }, line: { color: c[3], width: 2 } });
    txt(s, c[0], c[1], 5.82, w, 0.42, { fontFace: EN, fontSize: 12, color: c[4], align: "center", valign: "middle" });
    if (i < 3) txt(s, "→", c[1] + w, 5.82, 0.35, 0.42, { fontFace: EN, fontSize: 16, color: K.red, align: "center", valign: "middle" });
  });
  s.addText([
    { text: "只能依序前進。received 時顧客可直接取消；之後要申請退貨，由商店同意。", options: { fontFace: ZH, fontSize: 12, breakLine: true } },
    { text: "Forward-only. Cancel at “received”; later, a return needs store approval. Every change is logged.", options: { fontFace: EN2, fontSize: 10.5, color: K.mute } },
  ], { x: 0.85, y: 6.35, w: 9.6, h: 0.55, margin: 0, isTextBox: true, valign: "top" });
  s.addImage({ path: IMG("All.png"), x: 11.0, y: 5.35, w: 1.6, h: 1.58, altText: "mascot" });
  txt(s, "Source: Phase 2 SRS · BR-09 ~ BR-12, BR-19, BR-25", 7.2, 7.05, 4.6, 0.3, { fontFace: EN2, fontSize: 11, color: "A07D6C", align: "right" });
  notes(s, "(約 60 秒) 金額計算順序：小計 → 扣特殊活動折扣 → 扣季節性折扣 → 以折扣後金額算稅 5% → 加運費 100。範例：1000 元打 95 折得 950，稅 48，加運費 100 共 1,098。訂單狀態只能依序前進，received 時顧客可直接取消，之後要退貨需商店同意。");
}

// =====================================================================
// 9  END
// =====================================================================
{
  const s = pres.addSlide({ masterName: "HILLS" });
  s.addImage({ path: IMG("fuwa_title.png"), x: 4.4, y: 2.0, w: 4.5, h: 0.5, altText: "FUWA FUWA logo" });
  txt(s, "謝謝聆聽", 0, 2.75, 13.333, 1.0, { fontSize: 54, bold: true, color: K.brick, align: "center", valign: "middle" });
  txt(s, "Thank you · Q & A", 0, 3.75, 13.333, 0.6, { fontFace: EN, fontSize: 28, color: K.orange, align: "center", valign: "middle" });
  pill(s, "github.com/Frank05210000/database-project", 3.9, 4.65, 5.5, 0.5, { fill: K.peach, line: K.orange2, color: K.brown, size: 14 });
  [["hat.png", 1.6, 5.85, 1.3, 0.93], ["bow.png", 3.3, 5.9, 1.0, 0.84], ["can.png", 9.1, 6.0, 1.2, 0.71], ["collar.png", 10.8, 5.75, 1.0, 1.0]].forEach((p) => s.addImage({ path: IMG(p[0]), x: p[1], y: p[2], w: p[3], h: p[4], altText: p[0].replace(".png", "") }));
  notes(s, "(約 15 秒) 謝謝大家，歡迎提問。程式與文件都在 GitHub：Frank05210000/database-project。");
}

const out = path.join(__dirname, "FUWA_FUWA_e-Shop.pptx");
pres.writeFile({ fileName: out }).then(async () => {
  const SK = process.env.PPTX_SKILL;
  if (SK) {
    const { applyTheme } = require(path.join(SK, "scripts", "apply_theme.js"));
    await applyTheme(out, {
      name: "FUWA FUWA", headFontFace: ZH, bodyFontFace: ZH,
      colors: { dk1: "5D4037", lt1: "FFFFFF", dk2: "B05848", lt2: "FBEFB8", accent1: "D56B59", accent2: "E88D67", accent3: "F6BB6F", accent4: "FCDF8C", accent5: "6F9446", accent6: "FFE4B5", hlink: "D56B59", folHlink: "B05848" },
    });
  }
  console.log("wrote", out);
});
