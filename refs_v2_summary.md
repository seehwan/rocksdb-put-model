# Related Work Summaries (refs_v2.bib)

_Generated on 2025-09-07. Each item includes a 1–2 sentence contribution and why it matters for our put/compaction model._


## Foundations & Surveys

_Grounds our closed-form/dynamic models and the assumptions behind compaction and amplification._

- **The log-structured merge-tree (LSM-tree)** (Acta Informatica, 1996) — O'Neil, Patrick, Cheng, et al.
  - *Contribution.* Introduces the LSM-tree paradigm: batched, out-of-place writes with periodic merges to achieve write-optimized indexing.
  - *Why it matters.* Grounds our closed-form/dynamic models and the assumptions behind compaction and amplification.
  - *Link.* https://doi.org/10.1007/s002360050048
- **LSM-based Storage Techniques: A Survey** (The VLDB Journal, 2020) — Luo, Chen, Carey, et al.
  - *Contribution.* Comprehensive survey of LSM-based storage techniques—design choices, trade-offs, and system implications.
  - *Why it matters.* Grounds our closed-form/dynamic models and the assumptions behind compaction and amplification.
- **Structural Designs Meet Optimality: Exploring Optimized LSM-tree Structures in a Colossal Configuration Space** (Proceedings of the ACM on Management of Data, 2024) — Liu, Junfeng, Wang, et al.
  - *Contribution.* Explores a colossal configuration space to search for optimal LSM structural designs automatically.
  - *Why it matters.* Grounds our closed-form/dynamic models and the assumptions behind compaction and amplification.
  - *Link.* https://doi.org/10.1145/3654978

## Compaction Theory & Tuning

_Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput._

- **bLSM: A General Purpose Log Structured Merge Tree** (Proceedings of the 2012 ACM SIGMOD International Conference on Management of Data, 2012) — Sears, Russell, Ramakrishnan, et al.
  - *Contribution.* Proposes bLSM with a merge scheduler and Bloom filter design to smooth performance and generalize LSM operation.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
- **Monkey: Optimal Navigable Key-Value Store** (Proceedings of the 2017 {ACM} {SIGMOD} International Conference on Management of Data, 2017) — Dayan, Niv, Athanassoulis, et al.
  - *Contribution.* Optimizes level-wise Bloom bits and merge policy to achieve near-Pareto optimal read–write trade-offs in LSMs.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
- **SlimDB: A Space-Efficient Key-Value Storage Engine for Semi-Sorted Data** (Proceedings of the VLDB Endowment, 2017) — Ren, Kai, Zheng, et al.
  - *Contribution.* Addresses an aspect of LSM design/performance relevant to write path or compaction.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
- **Dostoevsky: Better Space-Time Trade-Offs for LSM-Tree Based Key-Value Stores via Adaptive Removal of Superfluous Merging** (Proceedings of the 2018 {ACM} {SIGMOD} International Conference on Management of Data, 2018) — Dayan, Niv, Idreos, et al.
  - *Contribution.* Avoids superfluous merges via adaptive policies—bridges leveled and tiered compaction based on data hotness.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
  - *Link.* https://doi.org/10.1145/3183713.3196927
- **FPGA-Accelerated Compactions for LSM-based Key-Value Store** (18th {USENIX} Conference on File and Storage Technologies (FAST '20), 2020) — Zhang, Teng, Wang, et al.
  - *Contribution.* Offloads LSM compaction to FPGA to accelerate merge throughput and relieve CPU/IO bottlenecks.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
- **Rosetta: A Robust Space-Time Optimized Range Filter for Key-Value Stores** (Proceedings of the 2020 {ACM} {SIGMOD} International Conference on Management of Data, 2020) — Luo, Siqiang, Chatterjee, et al.
  - *Contribution.* Robust space–time optimized range filter (Rosetta) complementing Bloom/SuRF for mixed point/range queries.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
  - *Link.* https://doi.org/10.1145/3318464.3389731
- **Constructing and Analyzing the LSM Compaction Design Space** (Proceedings of the VLDB Endowment, 2021) — Sarkar, Subhadeep, Staratzis, et al.
  - *Contribution.* Formalizes the compaction design space—triggers, layouts, granularity, and movement policies—with empirical evaluation.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
  - *Link.* https://doi.org/10.14778/3476249.3476274
- **Endure** (Proceedings of the VLDB Endowment, 2022) — Huynh, Andy, Chaudhari, et al.
  - *Contribution.* Robust LSM tuning under workload uncertainty; seeks parameter settings with strong worst-case guarantees.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
  - *Link.* https://doi.org/10.14778/3529337.3529345
- **Spooky: Granulating LSM-tree Compactions Correctly** (Proceedings of the VLDB Endowment, 2022) — Dayan, Niv, Luo, et al.
  - *Contribution.* Correctly accounts for transient/durable space amplification and the interaction of SSD GC with compaction.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
  - *Link.* https://doi.org/10.14778/3551793.3551853
- **Efficient Compactions Between Storage Tiers with PrismDB** (Proceedings of the 28th ACM International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS '23), 2023) — Raina, Ashwini, Lu, et al.
  - *Contribution.* Cost-aware cross-tier compaction/migration to balance performance and cloud storage cost.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
- **Rethinking the Compaction Policies in LSM-trees** (Proceedings of the {ACM} on Management of Data, 2025) — Wang, Hengrui, Qiu, et al.
  - *Contribution.* Automates compaction policy/parameter selection from workload characteristics for improved efficiency.
  - *Why it matters.* Informs parameterization (leveling/tiering, Bloom bits, triggers) that determines steady-state put throughput.
  - *Link.* https://doi.org/10.1145/3725344

## Write Amplification & KV-Separation

_Directly impacts the write budget our model accounts for by reducing bytes rewritten during compaction._

- **WiscKey** (14th {USENIX} Conference on File and Storage Technologies (FAST '16), 2016) — Lu, Lanyue, Pillai, et al.
  - *Contribution.* Key–value separation: stores values in a log to avoid rewriting large values during compaction, cutting write amplification on SSDs.
  - *Why it matters.* Directly impacts the write budget our model accounts for by reducing bytes rewritten during compaction.
- **PebblesDB: Building Key-Value Stores using Fragmented Log-Structured Merge Trees** (Proceedings of the 26th ACM Symposium on Operating Systems Principles (SOSP '17), 2017) — Raju, Pandian, Kadekodi, et al.
  - *Contribution.* FLSM (fragmented levels) reduces data re-write during compaction while sustaining high write throughput.
  - *Why it matters.* Directly impacts the write budget our model accounts for by reducing bytes rewritten during compaction.
  - *Link.* https://doi.org/10.1145/3132747.3132765
- **HashKV** ({USENIX} Annual Technical Conference (USENIX ATC '18), 2018) — Chan, Helen H. W., Li, et al.
  - *Contribution.* HashKV groups updates by hash to make KV-separation friendly to garbage collection and update-heavy workloads.
  - *Why it matters.* Directly impacts the write budget our model accounts for by reducing bytes rewritten during compaction.
- **HashKV** (ACM Transactions on Storage, 2019) — Li, Yongkun, Chan, et al.
  - *Contribution.* Full journal version of HashKV with design and evaluation details for update-efficient KV-separation.
  - *Why it matters.* Directly impacts the write budget our model accounts for by reducing bytes rewritten during compaction.
- **MatrixKV** (2020 {USENIX} Annual Technical Conference (USENIX ATC '20), 2020) — Yao, Ting, Zhang, et al.
  - *Contribution.* Uses NVM 'matrix container' to absorb L0/L1 pressure, reducing write stalls and overall write amplification.
  - *Why it matters.* Directly impacts the write budget our model accounts for by reducing bytes rewritten during compaction.

## Stability, Stall & Scheduling

_Explains and mitigates stalls/tail latency that our v2.1/v3 models incorporate via stall duty and scheduling._

- **TRIAD** ({USENIX} Annual Technical Conference (USENIX ATC '17), 2017) — Balmau, Oana, Didona, et al.
  - *Contribution.* System co-design of memory, disk, and log to alleviate write amplification and improve foreground write throughput.
  - *Why it matters.* Explains and mitigates stalls/tail latency that our v2.1/v3 models incorporate via stall duty and scheduling.
- **Redesigning LSMs for Non-Volatile Memory with NoveLSM** ({USENIX} Annual Technical Conference (USENIX ATC '18), 2018) — Kannan, Sudarsun, Bhat, et al.
  - *Contribution.* Redesigns LSM for NVM: persistent data structures and in-place commits to reduce stalls and write amplification.
  - *Why it matters.* Explains and mitigates stalls/tail latency that our v2.1/v3 models incorporate via stall duty and scheduling.
- **ElasticBF** (2019 {USENIX} Annual Technical Conference (USENIX ATC '19), 2019) — Li, Yongkun, Tian, et al.
  - *Contribution.* Hotness-aware Elastic Bloom Filter that dynamically adapts memory to reduce read costs.
  - *Why it matters.* Explains and mitigates stalls/tail latency that our v2.1/v3 models incorporate via stall duty and scheduling.
- **On Performance Stability in LSM-based Storage Systems** (Proceedings of the VLDB Endowment, 2019) — Luo, Chen, Carey, et al.
  - *Contribution.* Studies performance stability and how compaction scheduling choices drive stalls and sustainable write rates.
  - *Why it matters.* Explains and mitigates stalls/tail latency that our v2.1/v3 models incorporate via stall duty and scheduling.
- **SILK** (2019 {USENIX} Annual Technical Conference (USENIX ATC '19), 2019) — Balmau, Oana, Dinu, et al.
  - *Contribution.* I/O scheduling for flush/compaction to prevent latency spikes and maintain stable tail latencies.
  - *Why it matters.* Explains and mitigates stalls/tail latency that our v2.1/v3 models incorporate via stall duty and scheduling.
- **Lethe: A Tunable Delete-Aware LSM Engine** (Proceedings of the 2020 {ACM} {SIGMOD} International Conference on Management of Data, 2020) — Sarkar, Subhadeep, Papon, et al.
  - *Contribution.* Delete-aware LSM engine (FADE) and layout strategies to reduce the cost of deletes and tombstones.
  - *Why it matters.* Explains and mitigates stalls/tail latency that our v2.1/v3 models incorporate via stall duty and scheduling.
- **Differentiated Key-Value Storage Management for Balanced I/O Performance** (2021 {USENIX} Annual Technical Conference (USENIX ATC '21), 2021) — Li, Yongkun, Chen, et al.
  - *Contribution.* Differentiates KV storage (e.g., separation choices, GC strategies) to balance I/O under mixed workloads.
  - *Why it matters.* Explains and mitigates stalls/tail latency that our v2.1/v3 models incorporate via stall duty and scheduling.

## Workload Modeling & Production Systems

_Validates modeling against production patterns and guides calibration/benchmark design._

- **X-Engine** (Proceedings of the 2019 {ACM} {SIGMOD} International Conference on Management of Data, 2019) — Huang, Gui, Cheng, et al.
  - *Contribution.* Alibaba’s X-Engine: tiered LSM with engineering optimizations for large-scale OLTP and bursty traffic.
  - *Why it matters.* Validates modeling against production patterns and guides calibration/benchmark design.
- **Characterizing, Modeling, and Benchmarking RocksDB Key-Value Workloads at Facebook** (18th {USENIX} Conference on File and Storage Technologies (FAST '20), 2020) — Cao, Zhichao, Dong, et al.
  - *Contribution.* Characterizes real RocksDB workloads and proposes a modeling/benchmarking methodology faithful to production traits.
  - *Why it matters.* Validates modeling against production patterns and guides calibration/benchmark design.
- **MyRocks** (Proceedings of the VLDB Endowment, 2020) — Matsunobu, Yoshinori, Dong, et al.
  - *Contribution.* Describes Facebook’s MyRocks: production-grade LSM engine in MySQL serving social graph workloads.
  - *Why it matters.* Validates modeling against production patterns and guides calibration/benchmark design.
  - *Link.* https://doi.org/10.14778/3415478.3415546
- **RocksDB: Evolution of Development Priorities in a Key-Value Store Serving Large-Scale Applications** (Communications of the ACM, 2021) — Dong, Siying, Kryczka, et al.
  - *Contribution.* Engineering narrative of RocksDB evolution and priority shifts when serving large-scale applications.
  - *Why it matters.* Validates modeling against production patterns and guides calibration/benchmark design.

## Filters & Range Queries

_Affects memory split and read cost terms that backpressure compactions in mixed workloads._

- **SuRF** (Proceedings of the 2018 {ACM} {SIGMOD} International Conference on Management of Data, 2018) — Zhang, Huanchen, Lim, et al.
  - *Contribution.* Succinct Range Filter (SuRF) enabling compact, fast prefiltering for range queries in LSM KV stores.
  - *Why it matters.* Affects memory split and read cost terms that backpressure compactions in mixed workloads.
- **REMIX** ({USENIX} Conference on File and Storage Technologies (FAST '21), 2021) — Zhong, Wenshao, Chen, et al.
  - *Contribution.* Provides a global view for range queries across SSTables to speed up multi-file scans in LSMs.
  - *Why it matters.* Affects memory split and read cost terms that backpressure compactions in mixed workloads.
- **SNARF** (Proceedings of the VLDB Endowment, 2022) — Vaidya, Kunal, Chatterjee, et al.
  - *Contribution.* A learning-enhanced, robust range filter that balances space and false positives across varied workloads.
  - *Why it matters.* Affects memory split and read cost terms that backpressure compactions in mixed workloads.
  - *Link.* https://doi.org/10.14778/3529337.3529347
- **Prefix Siphoning: Exploiting LSM-Tree Range Filters for Information Disclosure** (2023 {USENIX} Annual Technical Conference (USENIX ATC '23), 2023) — Kaufman, Adi, Hershcovitch, et al.
  - *Contribution.* Shows how LSM range filters can leak information (prefix siphoning) and discusses mitigations.
  - *Why it matters.* Affects memory split and read cost terms that backpressure compactions in mixed workloads.
- **Oasis: An Optimal Disjoint Segmented Learned Range Filter** (Proceedings of the VLDB Endowment, 2024) — Chen, Guanduo, He, et al.
  - *Contribution.* Oasis: an optimal disjoint segmented learned range filter achieving strong space–accuracy trade-offs.
  - *Why it matters.* Affects memory split and read cost terms that backpressure compactions in mixed workloads.
  - *Link.* https://doi.org/10.14778/3659437.3659447

## Learning/Adaptive LSM

_Suggests autotuning hooks to keep model parameters near-optimal under shifting workloads._

- **Learning to Optimize LSM-trees: Towards a Reinforcement Learning based Key-Value Store for Dynamic Workloads** (Proceedings of the {ACM} on Management of Data, 2023) — Mo, Dingheng, Chen, et al.
  - *Contribution.* Reinforcement-learning driven LSM tuning that adapts structures to dynamic workloads.
  - *Why it matters.* Suggests autotuning hooks to keep model parameters near-optimal under shifting workloads.
- **Towards Flexibility and Robustness of LSM Trees** (The VLDB Journal, 2024) — Huynh, Andy, Athanassoulis, et al.
  - *Contribution.* Argues for flexible, robust LSM designs—principles and mechanisms for broad workload coverage.
  - *Why it matters.* Suggests autotuning hooks to keep model parameters near-optimal under shifting workloads.
  - *Link.* https://doi.org/10.1007/s00778-023-00826-9
