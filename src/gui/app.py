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

from src.extractors.hybrid_extractor import extract_pages_hybrid
from src.extractors.page_ocr import _PSM_AUTO
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

SUCCESS = "#16A34A"
SURFACE = "#1E1E2E"


# ─── Evento de progresso ─────────────────────────────────────────────────────

class ProgressEvent:
    def __init__(self, kind: str, **kwargs):
        self.kind = kind
        self.data = kwargs


# ─── Janela principal ─────────────────────────────────────────────────────────

class PDFOcrApp(ctk.CTk):
    """Janela principal do PDF OCR Reader."""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        self._pdf_path: Path | None = None
        self._result: DocumentResult | None = None
        self._queue: queue.Queue[ProgressEvent] = queue.Queue()
        self._processing = False

        self._build_ui()
        self._poll_queue()

    # ─── Construção da interface ──────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_header()
        self._build_file_row()
        self._build_center_panel()
        self._build_footer()

    def _build_header(self):
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=SURFACE)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header, text="📄  PDF OCR Reader",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=24, pady=(16, 2), sticky="w")
        ctk.CTkLabel(
            header,
            text="Extração híbrida: texto nativo + OCR para páginas escaneadas",
            font=ctk.CTkFont(size=12), text_color="gray70",
        ).grid(row=1, column=0, padx=24, pady=(0, 14), sticky="w")

    def _build_file_row(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 4))
        row.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(
            row, text="Selecionar PDF", width=140, command=self._on_select_file,
        ).grid(row=0, column=0, padx=(0, 12))
        self._lbl_file = ctk.CTkLabel(
            row, text="Nenhum arquivo selecionado", text_color="gray60", anchor="w",
        )
        self._lbl_file.grid(row=0, column=1, sticky="ew")

    def _build_center_panel(self):
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.grid(row=2, column=0, sticky="nsew", padx=16, pady=4)
        panel.grid_columnconfigure(1, weight=1)
        panel.grid_rowconfigure(0, weight=1)
        self._build_options_panel(panel)
        self._build_log_panel(panel)

    def _build_options_panel(self, parent):
        frame = ctk.CTkFrame(parent, width=220, corner_radius=10, fg_color=SURFACE)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        frame.grid_propagate(False)

        ctk.CTkLabel(
            frame, text="⚙  Opções", font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 8))

        ctk.CTkLabel(frame, text="Idioma OCR:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=16, pady=(6, 0))
        self._lang_var = ctk.StringVar(value="por+eng")
        ctk.CTkEntry(frame, textvariable=self._lang_var, width=188).pack(padx=16, pady=(2, 8))

        ctk.CTkLabel(frame, text="Formato de saída:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=16)
        self._fmt_var = ctk.StringVar(value="JSON")
        ctk.CTkSegmentedButton(
            frame, values=["JSON", "TXT"], variable=self._fmt_var, width=188,
        ).pack(padx=16, pady=(2, 12))

        ctk.CTkLabel(frame, text="PSM (apenas para OCR):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=16)
        self._psm_var = ctk.StringVar(value="Auto")
        ctk.CTkSegmentedButton(
            frame, values=["Auto", "3", "11"], variable=self._psm_var, width=188,
        ).pack(padx=16, pady=(2, 12))

        self._hybrid_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame, text="Extração híbrida\n(nativo onde possível)",
            variable=self._hybrid_var, font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self._preprocess_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame, text="Pré-processar imagem\n(inversão, contraste)",
            variable=self._preprocess_var, font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def _build_log_panel(self, parent):
        frame = ctk.CTkFrame(parent, corner_radius=10, fg_color=SURFACE)
        frame.grid(row=0, column=1, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            frame, text="📋  Log de processamento",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(14, 6), sticky="w")
        self._log_text = ctk.CTkTextbox(
            frame, font=ctk.CTkFont(family="Consolas", size=11),
            activate_scrollbars=True, wrap="word",
        )
        self._log_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._log_text.configure(state="disabled")
        self._log("Selecione um arquivo PDF e clique em Processar.")

    def _build_footer(self):
        footer = ctk.CTkFrame(self, corner_radius=0, fg_color=SURFACE)
        footer.grid(row=3, column=0, sticky="ew")
        footer.grid_columnconfigure(2, weight=1)

        self._btn_process = ctk.CTkButton(
            footer, text="▶  Processar PDF", width=160, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_process, state="disabled",
        )
        self._btn_process.grid(row=0, column=0, padx=(16, 8), pady=12)

        self._btn_save = ctk.CTkButton(
            footer, text="💾  Salvar resultado", width=160, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_save, state="disabled",
            fg_color=SUCCESS, hover_color="#15803D",
        )
        self._btn_save.grid(row=0, column=1, padx=(0, 16), pady=12)

        self._progress = ctk.CTkProgressBar(footer, width=300)
        self._progress.grid(row=0, column=2, padx=(0, 16), pady=12, sticky="e")
        self._progress.set(0)

        self._lbl_status = ctk.CTkLabel(
            footer, text="Aguardando arquivo...",
            text_color="gray60", font=ctk.CTkFont(size=11),
        )
        self._lbl_status.grid(row=0, column=3, padx=(0, 16), pady=12)

    # ─── Handlers ────────────────────────────────────────────────────────────

    def _on_select_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar PDF",
            filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")],
        )
        if not path:
            return
        self._pdf_path = Path(path)
        self._lbl_file.configure(text=self._pdf_path.name, text_color="white")
        self._btn_process.configure(state="normal")
        self._btn_save.configure(state="disabled")
        self._result = None
        size_mb = self._pdf_path.stat().st_size / (1024 * 1024)
        with fitz.open(str(self._pdf_path)) as doc:
            pages = len(doc)
        self._log_clear()
        self._log(f"Arquivo: {self._pdf_path.name}")
        self._log(f"Tamanho: {size_mb:.1f} MB  |  Páginas: {pages}")
        self._log("Clique em 'Processar PDF' para iniciar.\n")
        self._set_status("Pronto")

    def _on_process(self):
        if not self._pdf_path or self._processing:
            return
        self._processing = True
        self._btn_process.configure(state="disabled", text="Processando...")
        self._btn_save.configure(state="disabled")
        self._log_clear()
        self._progress.set(0)

        lang = self._lang_var.get().strip() or "por+eng"
        fmt = self._fmt_var.get().lower()
        hybrid = self._hybrid_var.get()
        preprocess = self._preprocess_var.get()
        psm_raw = self._psm_var.get()
        psm = 3 if psm_raw == "3" else 11 if psm_raw == "11" else _PSM_AUTO

        threading.Thread(
            target=self._run_pipeline,
            args=(str(self._pdf_path), lang, fmt, hybrid, preprocess, psm),
            daemon=True,
        ).start()

    def _on_save(self):
        if not self._result:
            return
        fmt = self._fmt_var.get().lower()
        ext = ".json" if fmt == "json" else ".txt"
        out_path = filedialog.asksaveasfilename(
            title="Salvar resultado",
            initialfile=self._pdf_path.stem + "_ocr" + ext,
            defaultextension=ext,
            filetypes=[("JSON", "*.json")] if fmt == "json" else [("TXT", "*.txt")],
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

    # ─── Pipeline (thread separada) ───────────────────────────────────────────

    def _run_pipeline(self, pdf_path, lang, fmt, hybrid, preprocess, psm):
        try:
            self._emit("log", text=f"Iniciando: {Path(pdf_path).name}")

            # Metadados
            self._emit("log", text="[1/4] Lendo metadados...")
            metadata = extract_pdf_metadata(pdf_path)
            for k, v in metadata.to_dict().items():
                self._emit("log", text=f"       {k}: {v}")

            with fitz.open(pdf_path) as doc:
                total_pages = len(doc)

            document = DocumentResult(
                file_path=pdf_path,
                total_pages=total_pages,
                metadata=metadata,
            )

            self._emit("log", text=f"\n[2/4] Extraindo texto ({total_pages} páginas)...")
            count = 0

            for page_data in extract_pages_hybrid(
                pdf_path, lang=lang, verbose=False, preprocess=preprocess, psm=psm
            ):
                count += 1
                mode_tag = "[NATIVO]" if page_data.mode == "native" else "[OCR]"
                tables_tag = f" | {len(page_data.tables)} tab." if page_data.tables else ""
                self._emit(
                    "log",
                    text=f"  Pág {count}/{total_pages}: {mode_tag} {len(page_data.blocks)} blocos{tables_tag}",
                )
                self._emit("progress", value=count / total_pages * 0.75)

                page_result = analyze_page_layout(
                    page_data.page_number, page_data.blocks, page_data.img_size[1]
                )
                page_result.extraction_mode = page_data.mode
                page_result.tables = page_data.tables
                document.pages.append(page_result)

            # Imagens embutidas
            self._emit("log", text="\n[3/4] Extraindo imagens embutidas...")
            images_by_page = extract_embedded_images(pdf_path, lang=lang)
            for pr in document.pages:
                pr.embedded_images = images_by_page.get(pr.page_number, [])
            self._emit("progress", value=0.95)

            self._emit("log", text="\n[4/4] Finalizando...")
            self._emit("progress", value=1.0)
            self._emit("done", result=document)

        except Exception as e:
            import traceback
            self._emit("error", text=str(e), trace=traceback.format_exc())

    def _emit(self, kind, **kwargs):
        self._queue.put(ProgressEvent(kind, **kwargs))

    # ─── Polling da fila ──────────────────────────────────────────────────────

    def _poll_queue(self):
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
            self._set_status(f"Processando... {int(event.data['value'] * 100)}%")
        elif event.kind == "done":
            self._result = event.data["result"]
            self._processing = False
            self._btn_process.configure(state="normal", text="▶  Processar PDF")
            self._btn_save.configure(state="normal")
            pages = self._result.total_pages
            native = sum(1 for p in self._result.pages if p.extraction_mode == "native")
            tables = sum(len(p.tables) for p in self._result.pages)
            self._log(f"\n✅ Concluído!")
            self._log(f"   Páginas nativas : {native}/{pages}")
            self._log(f"   Tabelas extraídas: {tables}")
            self._log(f"\n💾 Clique em 'Salvar resultado' para exportar.")
            self._set_status(f"{native}/{pages} páginas nativas")
        elif event.kind == "error":
            self._processing = False
            self._btn_process.configure(state="normal", text="▶  Processar PDF")
            self._log(f"\n❌ Erro: {event.data['text']}")
            self._log(event.data.get("trace", ""))
            self._set_status("Erro")
            self._progress.set(0)

    # ─── Utilitários ─────────────────────────────────────────────────────────

    def _log(self, text: str):
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
