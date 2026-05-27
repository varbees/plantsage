---
name: rayalaseema-flora-report
description: Use when identifying plants from Rayalaseema or South India, generating botanical plus ethnomedicinal flora reports, researching Telugu/Ayurvedic names and uses, building personal plant field guides, or adding observations to a local species knowledge log.
---

# Rayalaseema Flora Report

## Trigger

Use this skill when the user:
- Uploads or references a plant photo from Rayalaseema, Srikalahasti, Tirupati, Kadapa, Kurnool, Anantapur, Chittoor, or nearby South Indian dry scrubland.
- Provides a plant name and asks for medicinal, Ayurvedic, ecological, Telugu, or cultural knowledge.
- Wants a personal flora-learning report or field identification guide.

## Regional Defaults

Focus on Rayalaseema, Andhra Pradesh: Tirupati, Srikalahasti, Kadapa/YSR, Anantapur, Kurnool, Chittoor, and Annamayya. Treat the ecological baseline as Deccan thorn scrub and Southern Tropical Thorn Forest unless evidence says otherwise.

Communities and local records to prioritize: Yanadi, Chenchu, Yerukala, Sugali/Lambadi, Konda Reddy, Seshachalam Biosphere Reserve studies, Lankamalleswara Wildlife Sanctuary records, and Chittoor/Kadapa/Kurnool district ethnobotanical papers.

Sacred context: Srikalahasti is a Shiva Pancha Bhuta temple, Vayu sthala. Include Shaiva, Vaishnava, temple, village ritual, and Telugu folk-practice context only when source-backed or clearly caveated.

## Research Order

Search in this order:
1. eFlora India and Indian floras for botanical ID and distribution.
2. Lankamalleswara WLS, Seshachalam, Chittoor, Kadapa, Kurnool, Tirupati ethnobotany records.
3. Vedavathy et al. 1997 Chittoor tribal medicine and Madhava Chetty district flora references when relevant.
4. Ayurveda sources for Sanskrit drug name, rasa, guna, virya, vipaka, karma, formulations, and cautions.
5. PubMed/PMC/DOI-backed phytochemistry and pharmacology.
6. GBIF and local agriculture/Telugu sources for occurrence and practical uses.

## Required Report Order

1. Plant ID card: scientific name, family, Telugu transliteration, Telugu script, confidence.
2. What it looks like: habit, leaves, flowers, fruit, quick field marks.
3. Where to find it in Rayalaseema: microhabitat, districts, seasonality, associated species.
4. Tribal and folk medicine: community, ailment, part, preparation, dosage or usage, source.
5. How to use it: practical preparation steps, quantity, route, frequency, and caution.
6. Ayurvedic profile: classical name, rasa, guna, virya, vipaka, dosha action, karma, texts.
7. Active compounds: compound, class, activity, citation.
8. Safety: toxicity, toxic parts, contraindications, interactions, first aid.
9. Ecology: pollinators, wildlife value, invasive/native status, conservation.
10. Cultural significance: Srikalahasti/Shaiva context, festivals, folk beliefs, practical traditional use.
11. Field skills: ID tips, confusions, best observation season, forager notes.

## How To Use Section

Always include this section. For each use, include:
- Purpose.
- Part used.
- Preparation method in practical everyday language.
- Quantity, only when documented or explicitly caveated as traditional/approximate.
- How to take or apply.
- Frequency or timing.
- Caution.

Never replace this with vague phrases like "used medicinally." If a source does not provide usable quantities, say that quantities were not documented.

## Safety

- Prominently warn for toxic latex, seeds, berries, or roots.
- Never recommend internal use of Calotropis latex, Datura, Nerium, Lantana, or Gloriosa.
- Include first-aid notes for latex-eye exposure when relevant.
- Always state: consult a qualified Ayurvedic practitioner before internal use of any new herb.
- Keep medical advice educational and source-grounded.

## Output

When running in a code pipeline, produce valid JSON matching the PlantSage schema used by `agent/plant_agent.py`.

When answering directly in chat, use concise Markdown following the required report order. Include citations and caveats for scarce or conflicting evidence.
