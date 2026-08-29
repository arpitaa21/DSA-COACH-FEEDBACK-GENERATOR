import { useRef, useState } from 'react'

export default function ImageUpload({ imageFile, setImageFile }) {
  const inputRef = useRef(null)
  const [preview, setPreview] = useState(null)

  const onSelect = (file) => {
    if (!file) return
    setImageFile(file)
    setPreview(URL.createObjectURL(file))
  }

  return (
    <div className="panel p-4">
      <h3 className="font-mono font-bold text-sm mb-3 flex items-center gap-2">
        <span className="text-amber-500">02</span> Or upload a code photo / screenshot
      </h3>

      {!preview ? (
        <div
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); onSelect(e.dataTransfer.files?.[0]) }}
          className="cursor-pointer rounded-xl border-2 border-dashed border-paper-200 dark:border-ink-600 py-8 text-center hover:border-amber-400/60 transition-colors"
        >
          <p className="text-sm text-ink-600 dark:text-paper-200/60">
            Drop an image, or <span className="text-amber-500 font-medium">browse</span>
          </p>
          <p className="text-[11px] mt-1 text-ink-600/50 dark:text-paper-200/30">
            Handwritten notes, IDE screenshot, or a photo of your notebook — Gemini Vision reads the code for you
          </p>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => onSelect(e.target.files?.[0])}
          />
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <img src={preview} alt="uploaded code" className="w-20 h-20 object-cover rounded-lg border border-paper-200 dark:border-ink-600" />
          <div className="flex-1 text-sm">
            <p className="truncate">{imageFile?.name}</p>
            <button
              className="text-xs text-coral-400 mt-1 hover:underline"
              onClick={() => { setImageFile(null); setPreview(null) }}
            >
              Remove
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
