import fs from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'
import OpenAI from 'openai'

const usage = `
Usage:
  npm run asset:generate -- <prompt-file> <output-file> [--size 1536x1024] [--quality high]

Example:
  npm run asset:generate -- assets/prompts/stage-neon-dojo.md public/assets/generated/stage-neon-dojo.png --size 1536x1024 --quality high
`

function readOption(args, name, fallback) {
  const index = args.indexOf(name)
  if (index === -1) {
    return fallback
  }

  return args[index + 1] ?? fallback
}

const args = process.argv.slice(2)
const promptFile = args[0]
const outputFile = args[1]

if (!promptFile || !outputFile) {
  console.error(usage)
  process.exit(1)
}

if (!process.env.OPENAI_API_KEY) {
  console.error('Missing OPENAI_API_KEY. Set it before running asset generation.')
  process.exit(1)
}

const size = readOption(args, '--size', '1024x1024')
const quality = readOption(args, '--quality', 'medium')
const model = process.env.OPENAI_IMAGE_MODEL ?? 'gpt-image-2'
const prompt = await fs.readFile(promptFile, 'utf8')
const client = new OpenAI()

const response = await client.images.generate({
  model,
  prompt,
  size,
  quality,
})

const image = response.data?.[0]?.b64_json
if (!image) {
  console.error('The image API response did not include base64 image data.')
  process.exit(1)
}

await fs.mkdir(path.dirname(outputFile), { recursive: true })
await fs.writeFile(outputFile, Buffer.from(image, 'base64'))

const recordFile = `${outputFile}.prompt.txt`
await fs.writeFile(
  recordFile,
  [`model=${model}`, `size=${size}`, `quality=${quality}`, '', prompt].join('\n'),
)

console.log(`Wrote ${outputFile}`)
console.log(`Wrote ${recordFile}`)
