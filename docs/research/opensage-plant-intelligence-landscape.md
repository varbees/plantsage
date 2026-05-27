# OpenSage Plant Intelligence Landscape

Date: 2026-05-27

This brief turns the current PlantSage prototype into an evidence-backed product and data direction. The near-term goal is modest but real: identify plants quickly, explain what is known, ask for missing evidence when confidence is weak, and build a durable observation map for India region by region.

## Product Thesis

Most plant apps stop at "this might be X" plus generic care text. PlantSage should behave more like a field research assistant:

- It identifies fast, but shows confidence, alternatives, and the exact visual evidence it used.
- It treats an upload as an observation, not a disposable chat message.
- It asks for a better photo only when needed: leaves, flowers, fruit, bark, habit, habitat, scale, GPS, or local name.
- It cites sources and separates taxonomy, ecology, ethnobotany, crop advice, toxicity, and preparation guidance.
- It accumulates personal familiarity: new, learning, familiar, expert.
- It builds a regional plant knowledge graph, starting with Rayalaseema and expanding across India.

## Competitor Map

| Product | Primary job | What the UX seems optimized for | Useful lesson for PlantSage | Gap we can exploit |
| --- | --- | --- | --- | --- |
| PictureThis | Consumer plant ID, care, disease, toxicity | Polished mobile app, photo-first cards, premium care flows | Broad feature packaging: ID, diagnosis, toxicity, expert help, database | It is broad and polished, but not source-first or regionally grounded for Indian wild flora. |
| Pl@ntNet | Citizen-science plant ID and biodiversity observation | Multi-photo observation, community validation, GBIF contribution | Cooperative learning, expert-weighted review, image quality filters, GPS-aware data | Strong ID/citizen-science layer, weaker practical "how do I use this plant safely here?" reports. |
| Seek by iNaturalist | Family-safe nature exploration | Live camera, badges, nearby species, privacy-preserving location | Fast feedback, local likelihood, no-account first run | Good for exploration, not a serious plant research dossier. |
| iNaturalist | Community biodiversity records | Observation feed, human IDs, research-grade status | Human confirmation and public biodiversity data pipeline | Expert loop is powerful but slow and not personalized into field reports. |
| Plantix | Crop disease diagnosis for farmers | Crop workflow, district alerts, treatment steps, weather/agronomy utilities | Actionability wins: diagnosis plus treatment, alerts, crop-cycle advice | Crop-specific; not made for wild plants, ethnobotany, or personal flora learning. |
| PlantSnap | Plant ID plus community/care | Social feed, "snap and learn", care assistant | Community and save-for-later mechanics | Less trustable for field use unless evidence, alternatives, and source trail are explicit. |
| Flora Incognita | Research-backed European flora ID | Clean scientific app, fact sheets, observations for conservation | Ad-free, offline-tolerant, conservation-grade positioning | Region-specific to Europe; India needs its own region and language model. |
| Blossom | Houseplant care and disease | Reminders, disease workflow, AI botanist, plant collection | Excellent care-management primitives: reminders, notes, photos, treatment plans | Houseplant-centered, subscription-heavy, not a biodiversity atlas. |
| Leafsnap | Leaf-based electronic field guide | High-quality comparative images by organ | Organ-specific visual references and field-guide discipline | Limited regional coverage; PlantSage needs leaves, flowers, fruit, bark, seedling, habit, and local context. |
| Google Lens | General visual search | Instant image-to-web matching | Speed and zero-friction entry | It is not a botanical system: no observation memory, no source-quality control, no structured plant schema. |

Key source notes:

- PictureThis markets instant plant ID, diagnosis, care guides, toxicity, expert consultation, and a large database of 10,000+ species: https://www.picturethisai.com/app
- Pl@ntNet states that observations are reviewed, expert votes weigh more, AI retrains periodically, low-quality images are filtered, and eligible observations flow to GBIF: https://plantnet.org/en/about/
- Seek emphasizes live camera ID, nearby species, badges, no registration, no user-data collection, and obscured location: https://www.inaturalist.org/pages/seek_app
- Plantix covers crop diagnosis, treatments, community advice, disease alerts, weather, and fertilizer calculators; Google Play currently says 30 major crops and 780+ plant damages: https://play.google.com/store/apps/details?id=com.peat.GartenBank
- Flora Incognita identifies 30,000+ species, saves observations, provides fact sheets, is free/ad-free, and works without constant internet: https://floraincognita.com/
- Blossom exposes the houseplant version of the loop: ID, disease diagnosis, reminders, weather alerts, notes, water calculator, AI botanist: https://apps.apple.com/us/app/blossom-plant-care-guide/id1487453649

## UX Patterns Worth Borrowing

The current PlantSage console should become an "observation workspace" rather than a dashboard full of raw backend state.

1. Photo-first intake
   The image is the anchor. Metadata should stay compact: date, place, district, GPS precision, upload quality, organ detected.

2. Streaming research run
   Users should see a staged timeline: ingest, identify, verify, ground, synthesize, report. Each stage should show short useful text, not logs.

3. Confidence with next action
   If confidence is low, the app should not fail with a JSON blob. It should say: "I can see a seedling, but need leaves or flowers. Take one photo from the side and one close-up of the leaf arrangement."

4. Alternatives drawer
   Show top candidates with distinguishing traits. This is the missing layer in most ID apps and is essential for look-alikes.

5. Source stack
   A Perplexity-like source panel belongs inside the report: eFlora/IBIS/POWO/GBIF/medicinal/PubMed links with short evidence labels.

6. Region capsule
   Put "likely in this district/biome" next to the ID. India-scale plant ID should use geography as a first-class ranking feature.

7. Artifact canvas
   The right side of the desktop screen should be a live report canvas: overview, uses, ecology, safety, sources, PDF preview.

8. Memory rail
   A compact rail should show species already seen nearby, familiarity level, and last observation.

9. Field-safe language
   For medicinal or edible uses, default to caution: traditional use, source, preparation context, contraindications, and "do not ingest from this ID alone."

10. Export as an artifact
   Reports should feel like finished plant monographs, not chat transcripts.

## Open Design Lessons For OpenSage

The open-design repository is useful less as a UI kit and more as a product loop. Its README describes a local-first Claude Design alternative where a brief becomes an interactive question form, a selected visual direction, a live TodoWrite plan, a sandboxed artifact preview, and exportable HTML/PDF/ZIP outputs. It also uses skills, design systems, self-check checklists, SQLite persistence, and a local daemon/runtime split.

Source: https://github.com/nexu-io/open-design

PlantSage should adapt this pattern:

| Open Design pattern | OpenSage equivalent |
| --- | --- |
| Turn-1 discovery form | Ask for region, purpose, safety intent, and missing organ photos only when needed |
| Visual direction picker | Research mode picker: Field ID, Deep Monograph, Medicinal Safety, Crop Issue, Cultural/Ethnobotany |
| Live TodoWrite card | Live research run with visible stages and source count |
| Sandboxed artifact preview | Report canvas with structured Markdown/PDF preview |
| Skills catalog | Domain skills: Rayalaseema flora, crop diagnosis, Ayurvedic source audit, invasive species, conservation |
| Design systems | Region-aware report templates and map/field cards |
| Self-check | Botany schema validation, source quality audit, safety disclaimer, low-confidence gate |
| SQLite persistence | Local-first observation log, upgraded later to serverless Postgres |

The lesson is not to clone a generic chat app. The app should make the agent's work inspectable and interruptible while keeping the final artifact clean.

## Ten Pain Points To Beat

1. Seedlings and partial photos
   Many apps fail when only cotyledons, stems, bark, or blurred leaves are visible. PlantSage should detect insufficient evidence and ask for the exact missing organ.

2. Look-alike species
   The app must expose alternatives and distinguishing traits instead of overconfidently naming one plant.

3. Region-blind ranking
   A global model may suggest a visually similar plant that does not occur in the district. GPS, season, habitat, and Indian regional checklists should rerank candidates.

4. No source trail
   "Used medicinally" is not enough. Every claim needs source type, source link, and confidence.

5. Unsafe practical advice
   Edibility and medicinal preparation are high-risk. PlantSage should distinguish documented traditional use from safe personal use and should not generate medical advice as certainty.

6. Poor Indian language support
   Vernacular names are many-to-many and region-specific. Telugu/Hindi/Tamil/Kannada/Malayalam/Bengali/etc. names need provenance and ambiguity handling.

7. Thin observation memory
   Most apps identify and forget. PlantSage should build "my flora": where seen, when seen, life stage, familiarity, and revisits.

8. Weak offline/low-bandwidth story
   Field work often has poor network. PlantSage should capture locally, queue research, and show a provisional ID while deep research continues.

9. Ads/subscription friction
   Competitors often hide core flows behind premium prompts. The prototype should stay direct and serious: upload, identify, learn, save, export.

10. Data is hard to trust at India scale
   Indian flora data lives across government sites, citizen-science portals, global taxonomic databases, PDFs, and local-language literature. The system must store provenance and conflicts rather than flattening everything into one answer.

## India-Scale Data Source Strategy

The system should separate source roles instead of treating all sources equally.

### Taxonomy Spine

Use this to normalize names, synonyms, author citations, families, and accepted names.

- POWO / WCVP: global plant names, synonyms, distribution, descriptions, images. POWO currently advertises 1.448M plant names, 530.8K descriptions, and 514.8K images. https://powo.science.kew.org/
- IBIS Flora: Indian angiosperm checklist with accepted/provisional names, synonyms, distribution maps, bibliography, images, IUCN/NCBI/BHL links. The about page lists 21,764 species, 515 subspecies, 2,514 varieties, and 95,161 synonyms. https://www.indianbiodiversity.org/ibis-flora/
- Catalogue of Life / GBIF backbone: useful as a broad crosswalk and for stable IDs when ingesting occurrence data. https://www.gbif.org/

### Occurrence And Distribution

Use this to answer "is this likely here?"

- GBIF occurrence API: open biodiversity occurrence records, useful for map tiles, species ranges, and regional likelihood. https://techdocs.gbif.org/en/openapi/v1/occurrence
- iNaturalist/Pl@ntNet via GBIF where licensing permits; Pl@ntNet explicitly says qualified observations are shared to GBIF and GPS is crucial for mapping. https://plantnet.org/en/about/
- India Biodiversity Portal / IBIS maps and bibliography for India-specific distribution context. https://www.indianbiodiversity.org/ibis-flora/

### Indian Flora References

Use this to ground descriptions and regional flora.

- Botanical Survey of India books/PDFs and Flora of India volumes. BSI search results expose Flora of India PDFs with regional distribution and endemicity notes. https://bsi.gov.in/
- eFlora of India community pages and image-heavy species comparisons. Treat as useful but provenance-sensitive because it is community-run. https://efloraofindia.com/
- e-flora.co.in has accessible pages, but it appears to mix botanical content with commercial service links, so it should be lower priority than IBIS/BSI/eFloraofIndia. https://eflora.co.in/

### Medicinal, Cultural, And Use Data

Use this only with source labels and safety gating.

- NMPB medicinal list for official botanical-name coverage. https://nmpb.nic.in/medicinal_list
- Indian Medicinal Plants Database / FRLHT via Ministry of Ayush e-Charak: 7,263 botanical names, 150,000+ vernacular names in ten Indian languages, 5,000+ images, six medical systems and folk categories. https://echarak.ayush.gov.in/knowledge_resources?val=Map_Stackholder
- CCRAS database for references across botany, chemistry, pharmacology, pharmacy, and classical/modern literature. https://ccras.nic.in/documents/database-on-medicinal-plants/
- PubMed / PMC for modern biomedical evidence. Store abstracts/citations, not unsupported therapeutic claims.

### Images And Training/Evaluation

Use this for verification sets, not blind scraping.

- GBIF media records with license fields.
- eFloraofIndia species pages and comparison images, after checking reuse terms.
- User-contributed PlantSage observations with consent, SHA-256 image IDs, GPS precision, and review status.

## Region-By-Region Expansion Plan

India should be mapped by ecological and operational slices, not as one giant launch.

1. Rayalaseema / Seshachalam / Tirupati-Srikalahasti
   Start here because the product has local cultural context, Telugu naming, dry deciduous flora, temple/cultural uses, and user field observations.

2. Eastern Ghats corridor
   Expand into Andhra Pradesh, Telangana, Tamil Nadu, Odisha hill systems, focusing on dry forest, scrub, medicinal and endemic plants.

3. Western Ghats
   High endemism, high visual diversity, large public interest. Needs strong look-alike and conservation warnings.

4. Deccan Plateau and Central India
   Dry deciduous, agricultural edges, tribal ethnobotany, invasive species, medicinal shrubs.

5. Gangetic Plains
   Weeds, crops, wetlands, urban plants, medicinal/nitrogen-fixing trees.

6. Himalaya
   Elevation-aware ID, alpine species, medicinal plants, protected species, seasonality.

7. Northeast / Indo-Burma edge
   Orchid richness, high rainfall, high endemism, many languages, sensitive traditional knowledge.

8. Thar and arid northwest
   Xerophytes, desert shrubs, grazing/fodder uses, drought adaptation.

9. Coasts and mangroves
   Mangroves, halophytes, coastal medicinal/food species.

10. Andaman and Nicobar / Sundaland edge
   Island endemism, conservation sensitivity, careful data handling.

## Data Engineering Principles

The architecture should stay simple while respecting data-intensive-system realities.

1. Observations are append-only facts
   Never overwrite what the user saw. Corrections become new determinations linked to the same observation.

2. Separate writes from derived views
   Store raw observation, image metadata, model output, source citations, and report artifacts separately. Build species pages and dashboards as derived projections.

3. Every claim has provenance
   `report_sources` is a start. Next it should become `source_documents`, `claim_sources`, and `research_runs`.

4. Use idempotent ingestion
   Image SHA-256 already gives deduplication. Extend that to source ingestion with URL canonicalization and content hash.

5. Model output is untrusted input
   Parse with schemas, validate confidence, preserve raw response, and recover gracefully from malformed JSON.

6. Let long work be asynchronous
   Fast ID should return quickly. Deep report generation, PDF/image assets, source extraction, and map aggregation should run as jobs.

7. Prefer materialized read models
   Dashboards should not recompute from raw logs on every request. Build small summary tables or cached JSON views.

8. Design for conflicts
   Taxonomy changes, vernacular names conflict, and medicinal claims disagree. Store assertions with source, date, region, and confidence.

9. Keep local-first parity
   The local SQLite prototype is valuable. The production path should preserve the same ports: repository interface, object storage adapter, job queue adapter.

10. Add orchestration only when the runtime needs it
   Current Vercel/FastAPI can handle the prototype. Add a worker only for async research jobs; add containers only when PDF/system libraries or long-lived workers demand it.

## Proposed Serverless Architecture

Phase 1: Current prototype hardened

- Vercel/FastAPI endpoint for upload and fast ID.
- Gemini 2.5 Flash for image understanding and grounded research.
- SQLite locally; `/tmp` on Vercel only for previews.
- JSON/Markdown/PDF artifacts generated per run.
- Source stack visible in the UI.

Phase 2: Durable serverless production

- Vercel app for UI/API.
- Serverless Postgres for observations, species, determinations, research jobs, source documents, claims, and artifacts.
- Object storage for original images, resized derivatives, PDFs, and generated report images.
- Background job table plus scheduled/worker function for deep research and report generation.
- Gemini Search grounding for quick research; Gemini Deep Research / Interactions API for long-form monographs after job persistence exists.
- Optional Redis/queue only when job concurrency exceeds a Postgres-backed queue.

Phase 3: India map and learning loop

- Occurrence ingestion jobs from GBIF/IBIS/eFlora-derived allowed sources.
- Regional likelihood tables by species, district, month, habitat, and confidence.
- User review/correction flow.
- Expert review weight similar to Pl@ntNet, but scoped to PlantSage's own observations.
- Evaluation sets per region and plant organ.

## Schema Direction

The current tables should evolve toward these entities:

| Entity | Purpose |
| --- | --- |
| `observations` | Immutable field event: image, GPS, district, user note, timestamp, upload hash |
| `determinations` | One or more IDs for an observation, from model/user/expert, with confidence and evidence |
| `species` | Accepted taxon profile, normalized against POWO/IBIS/GBIF |
| `vernacular_names` | Name, language, script, region, source, ambiguity |
| `research_runs` | Agent run metadata, provider, model, mode, status, timings |
| `source_documents` | URL/PDF/book/source metadata, content hash, license, fetched_at |
| `plant_claims` | Structured assertions: use, toxicity, ecology, distribution, preparation, source-backed |
| `report_artifacts` | JSON/Markdown/PDF/images tied to a run |
| `region_occurrences` | Distribution evidence by species and geography |
| `review_events` | User/expert corrections, confirmations, and learning signal |

## UI Direction For The Next Build Pass

Desktop layout:

- Left: observation intake and photo quality checklist.
- Center: live agent run timeline and candidate stack.
- Right: report canvas with tabs: Summary, Evidence, Uses, Ecology, Sources, PDF.
- Bottom/right rail: local memory, recent species, familiarity, map hints.

Mobile layout:

- Stepper flow: Photo -> ID -> Ask/Retake if needed -> Report -> Save.
- Sticky confidence/action footer.
- Report sections as compact accordions.

Visual tone:

- Refined field-science utility, not a marketing landing page.
- Light, crisp, green-led palette with neutral paper surfaces and restrained yellow/blue status accents.
- Use plant imagery and specimen thumbnails as real content, not decorative backgrounds.
- Avoid showing backend config, raw JSON, or mock identities in the primary UI. Keep developer details behind a diagnostics drawer.

## Immediate Implementation Priorities

1. Keep the Gemini grounded-research provider as the default; Anthropic can remain a fallback, not the core dependency.
2. Replace visible raw error blobs with friendly low-confidence and parse-recovery states.
3. Add an async-ready `research_jobs` table even if the first implementation still runs synchronously.
4. Add candidate alternatives and missing-photo prompts to the identifier schema.
5. Add `source_documents` and `plant_claims` so reports become queryable knowledge, not only static files.
6. Redesign `app.html` into the observation workspace above.
7. Add a "Field ID" fast path that returns in a few seconds and a "Deep Report" job that can take longer.
8. Add PDF styling that includes the submitted image, confidence/evidence, source stack, and safety gating.
9. Add regional likelihood reranking using district/GPS and a seed table for Rayalaseema species.
10. Build a small evaluation set: 20 local images, expected species or genus, allowed uncertainty, and required next-question behavior.

