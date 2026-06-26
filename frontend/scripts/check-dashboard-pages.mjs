import { readdir, readFile } from "node:fs/promises"
import path from "node:path"

const rootDir = path.resolve(process.cwd(), "app", "(dashboard)")

async function collectPageFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true })
  const files = await Promise.all(
    entries.map(async (entry) => {
      const fullPath = path.join(dir, entry.name)

      if (entry.isDirectory()) {
        return collectPageFiles(fullPath)
      }

      return entry.name === "page.tsx" ? [fullPath] : []
    })
  )

  return files.flat()
}

const pageFiles = await collectPageFiles(rootDir)
const errors = []

for (const filePath of pageFiles) {
  const content = await readFile(filePath, "utf8")
  const relativePath = path.relative(process.cwd(), filePath)
  const defaultExports = content.match(/\bexport\s+default\b/g) ?? []

  if (/^\s*\/\/\s*\.\.\.\s*$/m.test(content)) {
    errors.push(`${relativePath}: contains literal stub marker "// ..."`)
  }

  if (defaultExports.length > 1) {
    errors.push(`${relativePath}: contains ${defaultExports.length} default exports`)
  }
}

if (errors.length > 0) {
  console.error("Dashboard page integrity check failed:\n")
  for (const error of errors) {
    console.error(`- ${error}`)
  }
  process.exit(1)
}

console.log(`Dashboard page integrity check passed for ${pageFiles.length} page files.`)
