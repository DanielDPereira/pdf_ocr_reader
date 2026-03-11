"""
Aplicação GUI do PDF OCR Reader.

Interface gráfica moderna construída com CustomTkinter.
Permite selecionar PDFs, ajustar opções de extração,
acompanhar o progresso em tempo real e salvar os resultados.

Como usar:
    python -m src.gui
"""

from __future__ import annotations

import json
import threading
import queue
import sys
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.extractors.page_ocr import extract_pages_ocr, _PSM_AUTO
from src.extractors.image_extractor import extract_embedded_images
from src.extractors.metadata_extractor import extract_pdf_metadata
from src.processors.layout_analyzer import analyze_page_layout
from src.models.document_model import DocumentResult

import fitz  # PyMuPDF


# ─── Tema e constantes visuais ────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_TITLE = "PDF OCR Reader"
APP_WIDTH = 920
APP_HEIGHT = 680
MIN_WIDTH = 760
MIN_HEIGHT = 520

ACCENT = "#2563EB"          # azul
ACCENT_HOVER = "#1D4FD8"
SUCCESS = "#16A34A"         # verde
WARNING = "#D97706"         # âmbar
ERROR_COLOR = "#DC2626"     # vermelho
SURFACE = "#1E1E2E"         # fundo das cards


# ─── Evento de progresso ─────────────────────────────────────────────────────

class ProgressEvent:
    """Evento enviado pela thread de OCR para a thread principal via queue."""

    def __init__(self, kind: str, **kwargs):
        self.kind = kind          # "log" | "progress" | "done" | "error"
        self.data = kwargs


# ─── Janela principal ─────────────────────────────────────────────────────────

class PDFOcrApp(ctk.CTk):
    """Janela principal do PDF OCR Reader."""

    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        # Estado interno
        self._pdf_path: Path | None = None
        self._result: DocumentResult | None = None
        self._queue: queue.Queue[ProgressEvent] = queue.Queue()
        self._processing = False

        self._build_ui()
        self._poll_queue()

    # ─── Construção da interface ──────────────────────────────────────────────

    def _build_ui(self):
        """Monta todos os elementos visuais."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # log área expande

        # Topo: título + subtítulo
        self._build_header()

        # Linha de seleção de arquivo
        self._build_file_row()

        # Painel central: opções (esq) + log (dir)
        self._build_center_panel()

        # Rodapé: botões de ação e barra de progresso
        self._build_footer()

    def _build_header(self):
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=SURFACE)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="📄  PDF OCR Reader",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=24, pady=(16, 2), sticky="w")

        ctk.CTkLabel(
            header,
            text="Extrai texto de PDFs — escaneados ou com texto nativo",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        ).grid(row=1, column=0, padx=24, pady=(0, 14), sticky="w")

    def _build_file_row(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 4))
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            row,
            text="Selecionar PDF",
            width=140,
            command=self._on_select_file,
        ).grid(row=0, column=0, padx=(0, 12))

        self._lbl_file = ctk.CTkLabel(
            row,
            text="Nenhum arquivo selecionado",
            text_color="gray60",
            anchor="w",
        )
        self._lbl_file.grid(row=0, column=1, sticky="ew")

    def _build_center_panel(self):
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.grid(row=2, column=0, sticky="nsew", padx=16, pady=4)
        panel.grid_columnconfigure(1, weight=1)
        panel.grid_rowconfigure(0, weight=1)

        # Painel de opções (esquerda)
        self._build_options_panel(panel)

        # Área de log (direita)
        self._build_log_panel(panel)

    def _build_options_panel(self, parent):
        frame = ctk.CTkFrame(parent, width=220, corner_radius=10, fg_color=SURFACE)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        frame.grid_propagate(False)

        ctk.CTkLabel(
            frame,
            text="⚙  Opções",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 8))

        # Idioma OCR
        ctk.CTkLabel(frame, text="Idioma OCR:", font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=16, pady=(6, 0)
        )
        self._lang_var = ctk.StringVar(value="por+eng")
        self._lang_entry = ctk.CTkEntry(frame, textvariable=self._lang_var, width=188)
        self._lang_entry.pack(padx=16, pady=(2, 8))

        # Formato de saída
        ctk.CTkLabel(frame, text="Formato de saída:", font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=16
        )
        self._fmt_var = ctk.StringVar(value="JSON")
        fmt_seg = ctk.CTkSegmentedButton(
            frame,
            values=["JSON", "TXT"],
            variable=self._fmt_var,
            width=188,
        )
        fmt_seg.pack(padx=16, pady=(2, 12))

        # PSM
        ctk.CTkLabel(frame, text="Segmentação (PSM):", font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=16
        )
        self._psm_var = ctk.StringVar(value="Auto")
        psm_seg = ctk.CTkSegmentedButton(
            frame,
            values=["Auto", "3 – Colunas", "11 – Esparso"],
            variable=self._psm_var,
            width=188,
        )
        psm_seg.pack(padx=16, pady=(2, 12))

        # Pré-processamento
        self._preprocess_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame,
            text="Pré-processamento de\nimagem (inversão, contraste)",
            variable=self._preprocess_var,
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=16, pady=(0, 16))

        # Info rápida
        info_text = (
            "PSM Auto detecta o modo\n"
            "por brilho da página.\n\n"
            "Pré-processamento melhora\n"
            "PDFs com fundo escuro\n"
            "ou fontes decorativas."
        )
        ctk.CTkLabel(
            frame,
            text=info_text,
            font=ctk.CTkFont(size=10),
            text_color="gray55",
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def _build_log_panel(self, parent):
        frame = ctk.CTkFrame(parent, corner_radius=10, fg_color=SURFACE)
        frame.grid(row=0, column=1, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="📋  Log de processamento",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(14, 6), sticky="w")

        self._log_text = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            activate_scrollbars=True,
            wrap="word",
        )
        self._log_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._log_text.configure(state="disabled")

        self._log("Selecione um arquivo PDF e clique em Processar.")

    def _build_footer(self):
        footer = ctk.CTkFrame(self, corner_radius=0, fg_color=SURFACE)
        footer.grid(row=3, column=0, sticky="ew")
        footer.grid_columnconfigure(2, weight=1)

        # Botão processar
        self._btn_process = ctk.CTkButton(
            footer,
            text="▶  Processar PDF",
            width=160,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_process,
            state="disabled",
        )
        self._btn_process.grid(row=0, column=0, padx=(16, 8), pady=12)

        # Botão salvar (aparece após processamento)
        self._btn_save = ctk.CTkButton(
            footer,
            text="💾  Salvar resultado",
            width=160,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_save,
            state="disabled",
            fg_color=SUCCESS,
            hover_color="#15803D",
        )
        self._btn_save.grid(row=0, column=1, padx=(0, 16), pady=12)

        # Barra de progresso
        self._progress = ctk.CTkProgressBar(footer, width=300)
        self._progress.grid(row=0, column=2, padx=(0, 16), pady=12, sticky="e")
        self._progress.set(0)

        # Status
        self._lbl_status = ctk.CTkLabel(
            footer,
            text="Aguardando arquivo...",
            text_color="gray60",
            font=ctk.CTkFont(size=11),
        )
        self._lbl_status.grid(row=0, column=3, padx=(0, 16), pady=12)

    # ─── Handlers ────────────────────────────────────────────────────────────

    def _on_select_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar PDF",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return

        self._pdf_path = Path(path)
        self._lbl_file.configure(
            text=self._pdf_path.name, text_color="white"
        )
        self._btn_process.configure(state="normal")
        self._btn_save.configure(state="disabled")
        self._result = None

        # Mostrar info básica do arquivo
        size_mb = self._pdf_path.stat().st_size / (1024 * 1024)
        with fitz.open(str(self._pdf_path)) as doc:
            pages = len(doc)
        self._log_clear()
        self._log(f"Arquivo: {self._pdf_path.name}")
        self._log(f"Tamanho: {size_mb:.1f} MB  |  Páginas: {pages}")
        self._log("Clique em 'Processar PDF' para iniciar a extração.\n")
        self._set_status("Pronto")

    def _on_process(self):
        if not self._pdf_path or self._processing:
            return

        self._processing = True
        self._btn_process.configure(state="disabled", text="Processando...")
        self._btn_save.configure(state="disabled")
        self._log_clear()
        self._log(f"Iniciando: {self._pdf_path.name}\n")
        self._progress.set(0)

        # Lê opções
        lang = self._lang_var.get().strip() or "por+eng"
        fmt = self._fmt_var.get().lower()
        preprocess = self._preprocess_var.get()
        psm_raw = self._psm_var.get()
        if "3" in psm_raw:
            psm = 3
        elif "11" in psm_raw:
            psm = 11
        else:
            psm = _PSM_AUTO

        # Lança thread de processamento
        thread = threading.Thread(
            target=self._run_ocr,
            args=(str(self._pdf_path), lang, fmt, preprocess, psm),
            daemon=True,
        )
        thread.start()

    def _on_save(self):
        if not self._result:
            return

        fmt = self._fmt_var.get().lower()
        ext = ".json" if fmt == "json" else ".txt"
        default = self._pdf_path.stem + "_ocr" + ext
        filetypes = (
            [("JSON", "*.json")] if fmt == "json" else [("Texto", "*.txt")]
        )

        out_path = filedialog.asksaveasfilename(
            title="Salvar resultado",
            initialfile=default,
            defaultextension=ext,
            filetypes=filetypes,
        )
        if not out_path:
            return

        try:
            if fmt == "json":
                self._result.save_json(out_path)
            else:
                self._result.save_txt(out_path)
            self._log(f"\n✅ Salvo em: {out_path}")
            self._set_status("Salvo!")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    # ─── Pipeline OCR (thread separada) ──────────────────────────────────────

    def _run_ocr(self, pdf_path: str, lang: str, fmt: str, preprocess: bool, psm: int):
        """Executa todo o pipeline de OCR. Roda em thread separada."""
        try:
            # 1. Metadados
            self._emit("log", text="[1/4] Lendo metadados...")
            metadata = extract_pdf_metadata(pdf_path)
            if metadata.to_dict():
                for k, v in metadata.to_dict().items():
                    self._emit("log", text=f"       {k}: {v}")

            # Determinar total de páginas para barra de progresso
            with fitz.open(pdf_path) as doc:
                total_pages = len(doc)

            # 2. OCR das páginas
            self._emit("log", text=f"\n[2/4] Extraindo texto ({total_pages} páginas)...")

            pages_data = []
            with fitz.open(pdf_path) as doc:
                for page_index in range(total_pages):
                    page_number = page_index + 1
                    page = doc[page_index]

                    from src.extractors.page_ocr import render_page_as_image, extract_ocr_blocks
                    image = render_page_as_image(page)
                    img_width, img_height = image.size
                    blocks, used_psm = extract_ocr_blocks(
                        image, page_number, lang=lang, preprocess=preprocess, psm=psm
                    )

                    psm_name = "sparse" if used_psm == 11 else "auto"
                    self._emit(
                        "log",
                        text=f"  Pág {page_number}/{total_pages}: PSM {used_psm} [{psm_name}] | {len(blocks)} blocos",
                    )
                    self._emit("progress", value=page_number / total_pages * 0.7)
                    pages_data.append((page_number, blocks, (img_width, img_height)))

            # 3. Imagens embutidas
            self._emit("log", text="\n[3/4] Extraindo imagens embutidas...")
            images_by_page = extract_embedded_images(pdf_path, lang=lang)
            self._emit("progress", value=0.85)

            # 4. Layout
            self._emit("log", text="\n[4/4] Analisando layout (header/body/footer)...")
            document = DocumentResult(
                file_path=pdf_path,
                total_pages=total_pages,
                metadata=metadata,
            )
            for page_number, blocks, (img_width, img_height) in pages_data:
                page_result = analyze_page_layout(page_number, blocks, img_height)
                page_result.embedded_images = images_by_page.get(page_number, [])
                document.pages.append(page_result)

            self._emit("progress", value=1.0)
            self._emit("done", result=document, fmt=fmt)

        except Exception as e:
            import traceback
            self._emit("error", text=str(e), trace=traceback.format_exc())

    def _emit(self, kind: str, **kwargs):
        """Envia evento da thread de OCR para a thread principal."""
        self._queue.put(ProgressEvent(kind, **kwargs))

    # ─── Polling da fila (thread principal) ──────────────────────────────────

    def _poll_queue(self):
        """Verifica a fila de eventos a cada 80ms e atualiza a UI."""
        try:
            while True:
                event = self._queue.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        self.after(80, self._poll_queue)

    def _handle_event(self, event: ProgressEvent):
        if event.kind == "log":
            self._log(event.data["text"])

        elif event.kind == "progress":
            self._progress.set(event.data["value"])
            pct = int(event.data["value"] * 100)
            self._set_status(f"Processando... {pct}%")

        elif event.kind == "done":
            self._result = event.data["result"]
            self._processing = False
            self._btn_process.configure(state="normal", text="▶  Processar PDF")
            self._btn_save.configure(state="normal")
            self._progress.set(1.0)

            pages = self._result.total_pages
            meta = self._result.metadata.to_dict()
            author = meta.get("author", "—")

            self._log(f"\n✅ Concluído!")
            self._log(f"   Páginas processadas: {pages}")
            self._log(f"   Autor: {author}")
            self._log(f"\n💾 Clique em 'Salvar resultado' para exportar.")
            self._set_status(f"Pronto — {pages} páginas")

        elif event.kind == "error":
            self._processing = False
            self._btn_process.configure(state="normal", text="▶  Processar PDF")
            self._log(f"\n❌ Erro: {event.data['text']}")
            self._log(event.data.get("trace", ""))
            self._set_status("Erro no processamento")
            self._progress.set(0)

    # ─── Utilitários de UI ────────────────────────────────────────────────────

    def _log(self, text: str):
        """Adiciona linha ao log na thread principal."""
        self._log_text.configure(state="normal")
        self._log_text.insert("end", text + "\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _log_clear(self):
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

    def _set_status(self, text: str):
        self._lbl_status.configure(text=text)
