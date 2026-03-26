import asyncio
import os
from pathlib import Path
from contractai_backend.modules.documents.infrastructure.llama_parser import LlamaParseExtractor

input_pdf = "/home/daminin/Documents/Repositorios/ContractAI-Backend/files/MODELO_DE_CONTRATO_DE_TRABAJO_SUJETO_A_MODALIDAD_.pdf"
output_md = "/home/daminin/Documents/Repositorios/ContractAI-Backend/files/CONTRATO_BETA.md"

async def main():


    if not os.path.exists(input_pdf):
        print(f"❌ Error: No se encuentra el archivo {input_pdf}")
        return

    print(f"🚀 Iniciando extracción de: {input_pdf}...")

    # 2. Instanciar tu extractor
    extractor = LlamaParseExtractor()

    try:
        # 3. Leer el archivo en bytes
        with open(input_pdf, "rb") as f:
            file_bytes = f.read()

        # 4. Llamar a tu método extract (que ya devuelve la lista de chunks con metadata)
        chunks = await extractor.extract(file=file_bytes, filename=input_pdf)

        print(f"✅ Se procesaron {len(chunks)} páginas.")

        with open(output_md, "w", encoding="utf-8") as f_out:
            for chunk in chunks:
                content = chunk["content"]
                metadata = chunk["metadata"]

                f_out.write(f"\n")
                f_out.write(content)
                f_out.write(f"\n\n\n---\n\n")

        print(f"✨ ¡Listo! El Markdown ha sido guardado en: {output_md}")

    except Exception as e:
        print(f"💥 Error durante la extracción: {str(e)}")


if __name__ == "__main__":
    # Ejecutamos el loop asíncrono
    asyncio.run(main())
