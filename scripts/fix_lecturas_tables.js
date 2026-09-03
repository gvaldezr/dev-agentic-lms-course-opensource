#!/usr/bin/env node
/*
 * fix_lecturas_tables.js
 *
 * Converts pipe-delimited markdown tables embedded inside the `texto` HTML
 * strings of docs/CV/js/lecturas.js into real HTML <table class="lectura-table">.
 *
 * Context: the original build collapsed markdown newlines, so every table row
 * (header | separator | body rows) ends up concatenated on a single line inside
 * a <p> element, e.g.:
 *   <p>Intro text: | Col A | Col B | |---|:---:| | a | b | | c | d |</p>
 *
 * This script:
 *   - Detects the markdown separator row (|---|:---:|---| ...) to identify a table.
 *   - Reconstructs header + body rows using the column count from the separator.
 *   - Emits <thead>/<tbody> with per-column alignment (:---: center, ---: right, --- left).
 *   - Preserves inline HTML already present inside cells (<strong>, &lt;, &gt;, etc.).
 *   - Keeps any leading text that preceded the table inside its own <p>.
 */

const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'docs', 'CV', 'js', 'lecturas.js');

/** Return the alignment for a separator cell like '---', ':---:', '---:', ':---'. */
function alignOf(sepCell) {
  const c = sepCell.trim();
  const left = c.startsWith(':');
  const right = c.endsWith(':');
  if (left && right) return 'center';
  if (right) return 'right';
  if (left) return 'left';
  return null; // default (left) -> omit style
}

/** True if a cell string is a markdown separator cell (only -, :, spaces, and >=2 dashes). */
function isSepCell(cell) {
  const c = cell.trim();
  return /^:?-{2,}:?$/.test(c);
}

/**
 * Split a raw pipe stream into logical cells.
 * The stream looks like: "| a | b | |---|---| | c | d |"
 * Splitting on '|' yields empty tokens at row boundaries which we drop,
 * but we must preserve grouping by using the known column count.
 */
function tokenizeCells(pipeStream) {
  // Split on '|' and trim; drop tokens that are purely empty (row separators / edges).
  return pipeStream
    .split('|')
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

/** Build the <td>/<th> cell HTML with optional alignment. */
function cellHtml(tag, content, align) {
  const style = align && align !== 'left' ? ` style="text-align:${align}"` : '';
  return `<${tag}${style}>${content}</${tag}>`;
}

/**
 * Given the array of cell tokens (header cells, then separator cells, then body cells)
 * and the number of columns, produce the <table> HTML.
 */
function buildTable(cells, ncols) {
  const header = cells.slice(0, ncols);
  const sep = cells.slice(ncols, ncols * 2);
  const bodyCells = cells.slice(ncols * 2);

  const aligns = sep.map(alignOf);

  const thead =
    '<thead><tr>' +
    header.map((h, i) => cellHtml('th', h, aligns[i])).join('') +
    '</tr></thead>';

  const rows = [];
  for (let i = 0; i < bodyCells.length; i += ncols) {
    const row = bodyCells.slice(i, i + ncols);
    // pad short trailing rows to ncols so markup stays valid
    while (row.length < ncols) row.push('');
    rows.push(
      '<tr>' + row.map((c, j) => cellHtml('td', c, aligns[j])).join('') + '</tr>'
    );
  }
  const tbody = '<tbody>' + rows.join('') + '</tbody>';

  return `<table class="lectura-table">${thead}${tbody}</table>`;
}

/**
 * Parse a single <p>...</p> inner text that may contain a pipe table.
 * Returns the transformed HTML (may be one or more block elements), or null
 * if no table was found (caller keeps original).
 */
function transformParagraph(inner) {
  // Locate the markdown separator row: a run like |---|:---:|--- ...|
  // We match the earliest position where a separator sequence begins.
  const sepMatch = inner.match(/\|\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|/);
  if (!sepMatch) return null;

  const sepStart = sepMatch.index;
  const sepEnd = sepStart + sepMatch[0].length;

  // The header row precedes the separator. Find where the pipe region starts:
  // walk backwards from sepStart to the first '|' that opens the header row.
  // The header is a contiguous "| ... | ... |" ending right before the separator.
  let headerStart = inner.lastIndexOf('|', sepStart - 1);
  // Move to the beginning of the header pipe-run (skip back over its cells).
  // Simplest robust approach: find the first '|' of the maximal pipe run that
  // ends at sepEnd-based table. We scan backward while the text between pipes
  // does not look like normal prose containing sentence punctuation runs.
  // In practice the header run is: "| cell | cell |" immediately before sep.
  // Find the start by locating the last '|' before the header cells begin.
  // We reconstruct by scanning backward pipe-by-pipe until we hit text that is
  // clearly not part of the table (no leading '|').
  // Header cell count is unknown yet; determine columns from the separator.
  const sepCells = tokenizeCells(sepMatch[0]);
  const ncols = sepCells.length;

  // Walk back from sepStart to capture exactly ncols header cells.
  // Collect '|' indices before sepStart.
  const pipeIdx = [];
  for (let k = 0; k < sepStart; k++) if (inner[k] === '|') pipeIdx.push(k);
  // The header occupies (ncols) cells => needs (ncols+1) pipes ending at the
  // pipe immediately before the separator. The pipe just before sepStart is the
  // closing pipe shared with the separator's opening; header uses the ncols
  // pipes before that as separators plus one opening pipe.
  // Header opening pipe = the (ncols+1)-th pipe counting back from sepStart.
  const closingHeaderPipe = pipeIdx[pipeIdx.length - 1]; // '|' right before sep
  const neededOpen = pipeIdx.length - (ncols + 1);
  headerStart = neededOpen >= 0 ? pipeIdx[neededOpen] : pipeIdx[0];

  const before = inner.slice(0, headerStart).trim();
  const tableRegion = inner.slice(headerStart, sepStart); // header pipe run
  // Everything after the separator is body (possibly followed by trailing prose,
  // but in this dataset the table runs to the end of the paragraph).
  const afterSep = inner.slice(sepEnd);

  // Detect any trailing prose after the final table pipe. Body rows are pipe runs;
  // trailing prose (if any) would appear after the last '|'. In this dataset the
  // paragraph ends right after the table, so afterSep is body content.
  const headerCells = tokenizeCells(tableRegion);
  const bodyCells = tokenizeCells(afterSep);

  const cells = headerCells.concat(sepCells, bodyCells);
  // Sanity: need at least header + separator worth of cells.
  if (headerCells.length < ncols) return null;

  const tableHtml = buildTable(cells, ncols);

  let out = '';
  if (before) out += `<p>${before}</p>`;
  out += tableHtml;
  return out;
}

/** Transform an entire `texto` HTML string, converting all embedded tables. */
function transformTexto(texto) {
  if (!/\|\s*:?-{2,}:?\s*\|/.test(texto)) return texto; // no separator -> no table

  // Split into <p>...</p> blocks while keeping non-<p> content intact.
  // We process block by block. Blocks are separated by "\n".
  const blocks = texto.split('\n');
  const outBlocks = blocks.map((block) => {
    const m = block.match(/^<p>([\s\S]*)<\/p>$/);
    if (!m) return block;
    const transformed = transformParagraph(m[1]);
    return transformed === null ? block : transformed;
  });
  return outBlocks.join('\n');
}

function main() {
  const src = fs.readFileSync(SRC, 'utf8');
  const m = src.match(/export const LECTURAS = (\{[\s\S]*\});?\s*$/);
  if (!m) {
    console.error('Could not locate LECTURAS object in', SRC);
    process.exit(1);
  }
  const header = src.slice(0, m.index); // preserve the comment banner
  const data = JSON.parse(m[1]);

  let converted = 0;
  let touchedLecturas = 0;
  for (const ada of Object.keys(data)) {
    data[ada].forEach((l) => {
      if (typeof l.texto === 'string' && /\|\s*:?-{2,}:?\s*\|/.test(l.texto)) {
        const before = l.texto;
        l.texto = transformTexto(l.texto);
        if (l.texto !== before) {
          touchedLecturas++;
          converted += (l.texto.match(/<table class="lectura-table">/g) || []).length;
        }
      }
    });
  }

  const out = `${header}export const LECTURAS = ${JSON.stringify(data)};`;
  fs.writeFileSync(SRC, out, 'utf8');
  console.log(`Lecturas updated: ${touchedLecturas}`);
  console.log(`Tables generated: ${converted}`);
}

main();
