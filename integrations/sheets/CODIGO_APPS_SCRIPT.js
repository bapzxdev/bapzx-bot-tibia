/**
 * BAPZX Tibia Coins - alimentacao automatica da planilha de clientes
 * ===================================================================
 * Este script recebe um POST do nosso bot (Render) com os dados de um
 * pedido e cria/atualiza a linha na planilha pelo id_pedido.
 *
 * CONFIGURACAO (fazer 1x, no Google Sheets):
 *   1. Abra a sua planilha de clientes -> Extensoes -> Apps Script.
 *   2. Cole TODO este codigo no editor e Salve (Ctrl+S).
 *   3. Rode uma vez a funcao "configurar" (Seletor no topo -> Executar):
 *        - Va ate a funcao configurar() abaixo, cole o SHEET_TOKEN no
 *          lugar de "COLE_AQUI_O_SHEET_TOKEN", selecione "configurar" e
 *          clique em Executar (aceite as permissoes).
 *        - Depois apague o texto "COLE_AQUI_O_SHEET_TOKEN" (o token ja
 *          ficou salvo com seguranca nas propriedades do script).
 *   4. Implantar -> Nova implantacao:
 *        Tipo: Aplicativo da web.
 *        Executar como: Eu
 *        Quem tem acesso: Qualquer pessoa
 *        Implantar. Copie a URL (https://script.google.com/macros/s/...
 *        /exec) -> essa URL vira SHEET_WEBAPP_URL.
 *
 * CAMPOS esperados no POST: {token, order:{data, cliente, contato, origem,
 * mundo, char, quantidade_tc, preco, tipo_pagamento, data_pagamento,
 * data_entrega, status, id_pedido, observacoes}}
 */
var COLUNAS = ['data', 'cliente', 'contato', 'origem', 'mundo', 'char',
  'quantidade_tc', 'preco', 'tipo_pagamento', 'data_pagamento',
  'data_entrega', 'status', 'id_pedido', 'observacoes'];

function configurar() {
  PropertiesService.getScriptProperties().setProperty('TOKEN', 'COLE_AQUI_O_SHEET_TOKEN');
  return 'Token salvo. Agora apague o valor das aspas e va em Implantar.';
}

function doPost(e) {
  var payload = {};
  try {
    payload = JSON.parse(e.postData.contents);
  } catch (err) {
    return json_({ ok: false, erro: 'json invalido' });
  }
  var esperado = PropertiesService.getScriptProperties().getProperty('TOKEN');
  if (!esperado || !payload.token || payload.token !== esperado) {
    return json_({ ok: false, erro: 'token invalido' });
  }
  var o = payload.order || {};
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('Dados') || ss.getActiveSheet();

  ensureHeader(sheet);
  var header = sheet.getRange(1, 1, 1, COLUNAS.length).getValues()[0];
  var colMap = {};
  for (var i = 0; i < header.length; i++) {
    colMap[String(header[i]).toLowerCase().trim()] = i;
  }

  var idPedido = String(o.id_pedido || '').trim();
  var linha = -1;
  if (colMap['id_pedido'] !== undefined && idPedido !== '') {
    var ultima = sheet.getLastRow();
    if (ultima > 1) {
      var idx = colMap['id_pedido'];
      var ids = sheet.getRange(2, idx + 1, ultima - 1, 1).getValues();
      for (var r = 0; r < ids.length; r++) {
        if (String(ids[r][0]).trim() === idPedido) { linha = r + 2; break; }
      }
    }
  }

  if (linha === -1) {
    var novaLinha = [];
    for (var c = 0; c < COLUNAS.length; c++) {
      novaLinha.push(o[COLUNAS[c]] !== undefined ? o[COLUNAS[c]] : '');
    }
    sheet.appendRow(novaLinha);
    return json_({ ok: true, acao: 'criada', linha: sheet.getLastRow() });
  }

  for (var col in COLUNAS) {
    var nome = COLUNAS[col];
    if (colMap[nome] === undefined) continue;
    var valor = o[nome] !== undefined ? o[nome] : '';
    sheet.getRange(linha, colMap[nome] + 1).setValue(valor);
  }
  return json_({ ok: true, acao: 'atualizada', linha: linha });
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Garante que a linha 1 da planilha seja EXATAMENTE a lista COLUNAS
 * (na mesma ordem). Assim o id_pedido fica sempre na coluna certa e o
 * update encontra a linha mesmo que a planilha tenha sido criado com
 * outro cabecalho (ex.: template v1 com 11 colunas).
 */
function ensureHeader(sheet) {
  var atual = [];
  var n = Math.min(sheet.getLastColumn(), COLUNAS.length);
  if (n >= 1) {
    atual = sheet.getRange(1, 1, 1, n).getValues()[0];
  }
  var igual = atual.length === COLUNAS.length;
  if (igual) {
    for (var i = 0; i < COLUNAS.length; i++) {
      if (String(atual[i]).toLowerCase().trim() !== COLUNAS[i]) { igual = false; break; }
    }
  }
  if (!igual) {
    sheet.getRange(1, 1, 1, COLUNAS.length).setValues([COLUNAS]);
  }
}