// @ts-nocheck
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

// claude-sonnet-4-6: resolve from cwd (ui/); import.meta.url isn't a file: URL under vitest
const readConfigView = (name: string) => readFileSync(resolve(process.cwd(), 'src/views/config', `${name}.tsx`), 'utf8')
const readLib = () => readFileSync(resolve(process.cwd(), 'src/lib/config.ts'), 'utf8')

describe('ConfigPage wiring', () => {
  it('loads sections and switches the active section', () => {
    const source = readConfigView('ConfigPage')

    expect(source).toContain('useSections')
    expect(source).toContain('setSelectedKey(item.key)')
    expect(source).toContain('core_config.company')
  })

  it('saves section values and keeps secrets masked', () => {
    const form = readConfigView('SectionForm')

    expect(form).toContain('useSaveSection')
    expect(form).toContain("values[field.key] === '••••'")
    expect(form).toContain('Rotate')
  })

  it('validates client-side before server save', () => {
    const form = readConfigView('SectionForm')

    expect(form).toContain('validateAll')
    expect(form).toContain('must be a number')
    expect(form).toContain('Use a hex color')
  })

  it('uses React Query cache invalidation for config mutations', () => {
    const source = readLib()

    expect(source).toContain('useMutation')
    expect(source).toContain("invalidateQueries({ queryKey: ['config'] })")
  })
})
