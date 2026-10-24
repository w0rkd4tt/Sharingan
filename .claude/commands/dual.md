# /dual — Dual Flow (Web + Whitebox)

## Usage
`/dual <TARGET> <REPO_PATH>`

## Steps
1. **Setup**: Create target dir, load scope, set env for both flows.
2. **Parallel launch**:
   - Start web flow Phase 1-2 (recon-web + mapper)
   - Start whitebox flow Steps 1-4 (recon-src + normalize + graph)
3. **Cross-flow bridge activation**:
   - Web recon tech_stack → whitebox advisory lookup
   - Whitebox routing.json → web mapper endpoint seeding
4. **Hunt phase** (both flows in parallel):
   - Web hunter-web ×N + Whitebox hunter-src ×N
   - Cross-flow chain candidates checked continuously
5. **Unified harvest**:
   - Merge primitives from both flows
   - Cross-flow chain matching (constraint-aware)
   - DUAL-CONFIRMED findings get highest priority
6. **Report**: Unified report combining both flows.
7. **Brain sync**: Full sync to SiYuan.
