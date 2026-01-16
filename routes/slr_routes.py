from flask import Blueprint, request, jsonify
from handlers.slr_handler import (
    handle_generate_pdf_notes,
    handle_parse_grammar,
    handle_augment_grammar,
    handle_compute_first_follow,
    handle_build_dfa,
    handle_generate_dfa_diagram,
    handle_build_parsing_table,
    handle_parse_string,
    handle_verify_grammar
)

slr_bp = Blueprint('slr', __name__)

slr_bp.route('/parse-grammar', methods=['POST'])(handle_parse_grammar)
slr_bp.route('/augment-grammar', methods=['POST'])(handle_augment_grammar)
slr_bp.route('/compute-first-follow', methods=['POST'])(handle_compute_first_follow)
slr_bp.route('/build-dfa', methods=['POST'])(handle_build_dfa)
slr_bp.route('/generate-dfa-diagram', methods=['POST'])(handle_generate_dfa_diagram)
slr_bp.route('/build-parsing-table', methods=['POST'])(handle_build_parsing_table)
slr_bp.route('/parse-string', methods=['POST'])(handle_parse_string)
slr_bp.route('/verify-grammar', methods=['POST'])(handle_verify_grammar)
slr_bp.route('/export-pdf',methods=["POST"])(handle_generate_pdf_notes)

