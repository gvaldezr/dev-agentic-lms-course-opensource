#!/usr/bin/env node
/*
 * add_lectura_resource_links.js
 *
 * Wraps the resource name portion of each DUA "Recursos complementarios" item
 * in docs/CV/js/lecturas.js with an <a href="URL" target="_blank" rel="noopener">
 * tag, using the verified URLs from artifacts/recursos_links_verificados.md.
 *
 * Resources live in the `recursos` array of each lectura (rendered raw as
 * <li>${r}</li> in app.js, so embedded HTML anchors render correctly).
 *
 * Matching is done by a stable key "ADA<ada> L<lectura> r<index>" so we target
 * the exact item, then we wrap the substring that starts at the first `"` (the
 * quoted title) and ends at the author segment, leaving the emoji/label prefix
 * and any trailing parenthetical (e.g. "(YouTube, 18 min)") outside the link.
 *
 * For 🔄 [ALTERNATIVA] resources we use the recommended alternative URL.
 * Items without a verified URL are intentionally left untouched.
 */

const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'docs', 'CV', 'js', 'lecturas.js');

// key -> verified URL (from recursos_links_verificados.md)
const URLS = {
  // ADA 1
  'ADA1 L1 r0': 'https://datareportal.com/reports/digital-2025-global-overview-report',
  'ADA1 L1 r1': 'https://sproutsocial.com/insights/index/',
  'ADA1 L2 r0': 'https://later.com/resources/videos/social-media-manager-day-in-the-life/',
  'ADA1 L2 r1': 'https://buffer.com/resources/social-media-report/',
  'ADA1 L2 r2': 'https://buffer.com/resources/science-of-social-media/',
  'ADA1 L3 r0': 'https://thehustle.co/how-duolingo-struck-social-gold-by-going-unhinged',
  'ADA1 L3 r1': 'https://sproutsocial.com/insights/duolingo-tiktok-success/',
  'ADA1 L3 r2': 'https://themarketingmillennials.com/podcast/',
  'ADA1 L4 r0': 'https://vilmanunez.com/training-community-manager/',
  'ADA1 L4 r1': 'https://buffer.com/resources/social-media-report/',
  // ADA 2
  'ADA2 L1 r0': 'https://neilpatel.com/blog/what-does-a-profitable-social-media-sales-funnel-look-like/',
  'ADA2 L1 r1': 'https://offers.hubspot.com/social-media-strategy-workbook',
  'ADA2 L2 r0': 'https://metricool.com/es/que-es-whatsapp-business/',
  'ADA2 L3 r0': 'https://academy.hubspot.com/courses/buyer-persona',
  'ADA2 L3 r1': 'https://blog.hubspot.com/marketing/buyer-persona-research',
  'ADA2 L3 r2': 'https://podcasts.apple.com/us/podcast/everyone-hates-marketers-no-bs-marketing-brand-strategy/id1221256195',
  'ADA2 L4 r0': 'https://vilmanunez.com/copywriting-estrategia-marketing-online/',
  'ADA2 L4 r2': 'https://copyblogger.com/rainmaker-fm',
  // ADA 3
  'ADA3 L1 r0': 'https://later.com/blog/brand-voice/',
  'ADA3 L1 r1': 'https://styleguide.mailchimp.com/voice-and-tone/',
  'ADA3 L1 r2': 'https://podcasts.apple.com/us/podcast/the-futur-with-chris-do/id1209219220',
  'ADA3 L1 r3': 'https://sproutsocial.com/insights/brand-voice/',
  'ADA3 L2 r0': 'https://vilmanunez.com/que-es-una-marca-personal-ejemplos/',
  'ADA3 L3 r0': 'https://later.com/blog/user-generated-content/',
  'ADA3 L4 r0': 'https://www.canva.com/learn/your-brand-needs-a-visual-style-guide/',
  'ADA3 L4 r1': 'https://www.canva.com/docs/brand-guidelines/',
  'ADA3 L4 r2': 'https://podcasts.apple.com/us/podcast/the-futur-with-chris-do/id1209219220',
  // ADA 4
  'ADA4 L1 r0': 'https://metricool.com/es/calendario-editorial/',
  'ADA4 L1 r1': 'https://blog.hootsuite.com/social-media-calendar/',
  'ADA4 L2 r0': 'https://later.com/blog/instagram-reels/',
  'ADA4 L2 r2': 'https://www.socialmediaexaminer.com/social-media-marketing-podcast/',
  'ADA4 L3 r0': 'https://neilpatel.com/blog/grow-team-influencers/',
  'ADA4 L4 r0': 'https://later.com/blog/best-ai-social-media-tools-2026/',
  'ADA4 L4 r1': 'https://blog.hubspot.com/marketing/chatgpt-prompts',
  'ADA4 L4 r2': 'https://marketingagainstthegrain.com/',
  'ADA4 L5 r0': 'https://youtu.be/V8J36NxXRhw',
  'ADA4 L5 r2': 'https://www.hubspot.com/ads-calculator',
  // ADA 5
  'ADA5 L1 r0': 'https://sproutsocial.com/insights/social-media-metrics/',
  'ADA5 L1 r1': 'https://portermetrics.com/en/templates/google-looker-studio/free-social-media-insights/',
  'ADA5 L1 r2': 'https://www.marketingovercoffee.com/',
  'ADA5 L2 r0': 'https://later.com/blog/instagram-analytics/',
  'ADA5 L2 r1': 'https://metricool.com/es/mega-tutorial-metricool/',
  'ADA5 L2 r2': 'https://blog.hootsuite.com/instagram-analytics/',
  'ADA5 L3 r0': 'https://blog.hootsuite.com/social-media-roi/',
  'ADA5 L3 r1': 'https://www.hootsuite.com/social-media-tools/social-media-roi-calculator',
  'ADA5 L3 r2': 'https://buffer.com/resources/social-media-report/',
  'ADA5 L4 r0': 'https://buffer.com/resources/how-buffer-ab-tests/',
  'ADA5 L4 r1': 'https://buffer.com/resources/marketing-spreadsheets/',
  'ADA5 L4 r2': 'https://podcasts.apple.com/us/podcast/social-media-marketing-podcast/id549899114',
  'ADA5 L5 r0': 'https://www.socialmediaexaminer.com/7-creative-social-media-marketing-mini-case-studies/',
  'ADA5 L5 r1': 'https://neilpatel.com/blog/data-driven-marketing/',
  'ADA5 L5 r2': 'https://support.google.com/looker-studio/',
  'ADA5 L5 r3': 'https://podcasts.apple.com/ao/podcast/the-marketing-book-podcast/id961463317',
};

/**
 * Wrap the name portion of a resource string in an anchor.
 * A resource looks like:  '<emoji> <Label>: "<Title>" — <Author> (<parenthetical>)'
 * We link from the first '"' up to (but not including) any trailing " (...)".
 * If there's no quoted title (rare), we link the segment after the ':' label.
 * Returns { html, ok }.
 */
function linkify(resource, url) {
  if (resource.includes('<a ')) return { html: resource, ok: false }; // already linked

  const open = `<a href="${url}" target="_blank" rel="noopener">`;
  const close = '</a>';

  // Find the label separator ": " that precedes the resource name.
  const labelIdx = resource.indexOf(': ');
  if (labelIdx === -1) return { html: resource, ok: false };

  const prefix = resource.slice(0, labelIdx + 2); // includes ": "
  let body = resource.slice(labelIdx + 2);

  // Split off a trailing parenthetical like " (YouTube, 18 min)" to keep it outside the link.
  let trailer = '';
  const parenMatch = body.match(/\s*\([^()]*\)\s*$/);
  if (parenMatch) {
    trailer = body.slice(parenMatch.index);
    body = body.slice(0, parenMatch.index);
  }

  body = body.trim();
  if (!body) return { html: resource, ok: false };

  const html = `${prefix}${open}${body}${close}${trailer}`;
  return { html, ok: true };
}

function main() {
  const src = fs.readFileSync(SRC, 'utf8');
  const m = src.match(/export const LECTURAS = (\{[\s\S]*\});?\s*$/);
  if (!m) {
    console.error('Could not locate LECTURAS object in', SRC);
    process.exit(1);
  }
  const header = src.slice(0, m.index);
  const data = JSON.parse(m[1]);

  let linked = 0;
  let skipped = 0;
  const missing = [];

  for (const ada of Object.keys(data)) {
    data[ada].forEach((l, i) => {
      if (!Array.isArray(l.recursos)) return;
      l.recursos = l.recursos.map((r, ri) => {
        const key = `ADA${ada} L${i + 1} r${ri}`;
        const url = URLS[key];
        if (!url) {
          skipped++;
          return r;
        }
        const { html, ok } = linkify(r, url);
        if (ok) linked++;
        else missing.push(key);
        return html;
      });
    });
  }

  const out = `${header}export const LECTURAS = ${JSON.stringify(data)};`;
  fs.writeFileSync(SRC, out, 'utf8');
  console.log(`Resources linked: ${linked}`);
  console.log(`Resources left as-is (no verified URL): ${skipped}`);
  if (missing.length) console.log('Had URL but could not linkify:', missing.join(', '));
}

main();
