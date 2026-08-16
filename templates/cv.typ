#set page(paper: "a4", margin: (x: 2cm, y: 1.8cm))
#set text(font: "New Computer Modern", size: 10pt)
#set par(justify: false, leading: 0.56em, spacing: 0pt)
#set list(marker: [•], tight: false, spacing: 0.35em)

#let rule-gray = block(spacing: 0pt, line(length: 100%, stroke: 0.6pt + gray))
#let fa-solid(code) = text(font: "Font Awesome 5 Free", size: 9.5pt, baseline: -1pt)[#str.from-unicode(code)]
#let fa-brands(code) = text(font: "Font Awesome 5 Brands", size: 9.5pt, baseline: -1pt)[#str.from-unicode(code)]

#show heading.where(level: 1): it => {
  v(10pt)
  text(size: 11.5pt, weight: "bold")[#it.body]
  v(3pt)
  rule-gray
  v(5pt)
}

#align(center)[
  #text(size: 18pt, weight: "bold")[Samir Haddad]
  #v(3pt)
  *Senior Backend Engineer*  #h(3pt) — #h(3pt)  Cairo, Egypt  (Remote)
  #v(6pt)
  #text(size: 9.5pt)[
    #fa-solid(0xf0e0)  samir.haddad\@example.com
    #h(14pt)
    #fa-brands(0xf09b)  github.com/samirh
    #h(14pt)
    #fa-brands(0xf08c)  linkedin.com/in/samirh
  ]
  #v(8pt)
  #rule-gray
]

= Summary
Backend engineer with 8 years building high-traffic services in Python and Go.
Designed payment systems processing USD 2M+ monthly across 3 regions.

= Experience

*NilePay* — _Senior Backend Engineer_, 2021--2026
- Led migration from a monolith to 14 microservices, cutting deploy time 70%
- Built idempotent payment API handling 4,000 req/s at 99.95% uptime
- Mentored 5 engineers; introduced code-review and CI standards

#v(5pt)
*CleverCloud* — _Backend Engineer_, 2018--2021
- Shipped event-driven ingestion pipeline (Kafka + Go) for 200M events/day
- Cut query latency 60% by moving reporting to a columnar store

#v(5pt)
*TechStack* — _Junior Engineer_, 2016--2018
- Built REST APIs in Python/Django; introduced automated testing, 80% coverage

= Skills
#grid(
  columns: (auto, 1fr),
  column-gutter: 12pt,
  row-gutter: 4pt,
  [*Languages:*], [Python, Go, TypeScript],
  [*Data:*], [PostgreSQL, Redis, Kafka, ClickHouse],
  [*Cloud:*], [AWS, Docker, Kubernetes, Terraform],
)

= Education
*B.Sc. Computer Science* — Cairo University, 2012--2016
