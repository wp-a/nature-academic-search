/**
 * Bundle metadata entry for DeepSeek Harness.
 *
 * The runtime contribution is declared in cordis.patch.yml. Keeping this
 * module side-effect free lets a profile inspect the package without starting
 * the external Python MCP process.
 */
export const name = 'dsh-academic-paper-search'

export function apply() {}
