import CoreGraphics
import Foundation
import ImageIO
import Vision

struct OCRResult: Codable {
    let path: String
    let status: String
    let text: String
    let reason: String
}

func emit(_ result: OCRResult) {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.withoutEscapingSlashes]
    if let data = try? encoder.encode(result), let line = String(data: data, encoding: .utf8) {
        print(line)
    }
}

for path in CommandLine.arguments.dropFirst() {
    let url = URL(fileURLWithPath: path)
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        emit(OCRResult(path: path, status: "source_image_unreadable", text: "", reason: "image could not be loaded"))
        continue
    }

    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]

    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    do {
        try handler.perform([request])
        let lines = (request.results ?? []).compactMap { observation in
            observation.topCandidates(1).first?.string
        }
        let text = lines.joined(separator: "\n").trimmingCharacters(in: .whitespacesAndNewlines)
        if text.isEmpty {
            emit(OCRResult(path: path, status: "no_text_from_engine", text: "", reason: "vision returned no OCR text"))
        } else {
            emit(OCRResult(path: path, status: "ocr_text_available", text: text, reason: ""))
        }
    } catch {
        emit(OCRResult(path: path, status: "ocr_engine_error", text: "", reason: "\(error)"))
    }
}
