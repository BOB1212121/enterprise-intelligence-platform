'use strict';

// ── Constants ─────────────────────────────────────────────────────────────────

const EIP_API = {
	GET:    'enterprise_intelligence_platform.api.recommendations.get_ai_recommendations',
	ACCEPT: 'enterprise_intelligence_platform.api.recommendations.accept_recommendation',
	REJECT: 'enterprise_intelligence_platform.api.recommendations.reject_recommendation',
};

const EIP_STATUS = {
	PENDING:  'pending',
	LOADING:  'loading',
	ACCEPTED: 'accepted',
	REJECTED: 'rejected',
	DEFERRED: 'deferred',
	ERROR:    'error',
};

const EIP_CONF_COLOR = { High: 'green', Medium: 'orange', Low: 'red' };

const EIP_CLASS_COLOR = {
	Preventive:          'blue',
	Corrective:          'red',
	Optimizing:          'green',
	'Learning-Oriented': 'purple',
};

const EIP_DIR_ARROW = { Increase: '↑', Decrease: '↓', Stable: '→' };

const EIP_ANALYSIS_TIMEOUT_MS = 90_000;
const EIP_STYLE_ID             = 'eip-page-styles';

// ── CSS ───────────────────────────────────────────────────────────────────────

const EIP_CSS = `
.eip-wrap {
	padding: var(--padding-lg, 16px);
	max-width: 960px;
	margin: 0 auto;
}

/* ── Controls bar ── */
.eip-controls-bar {
	display: flex;
	align-items: flex-end;
	gap: 12px;
	margin-bottom: 16px;
	flex-wrap: wrap;
}
.eip-charter-wrap { flex: 1 1 360px; }
.eip-charter-wrap .frappe-control { margin-bottom: 0; }
.eip-analyse-btn  { flex-shrink: 0; }

/* ── Status bar ── */
.eip-status-bar {
	display: flex;
	align-items: center;
	gap: 8px;
	min-height: 28px;
	margin-bottom: 16px;
	flex-wrap: wrap;
}
.eip-ts { font-size: 12px; color: var(--text-muted); }

/* ── States ── */
.eip-empty-state,
.eip-loading-area {
	text-align: center;
	padding: 60px 20px;
	color: var(--text-muted);
}
.eip-empty-icon { font-size: 40px; margin-bottom: 12px; }

.eip-spinner {
	display: inline-block;
	width: 40px; height: 40px;
	border: 3px solid var(--gray-300, #e4e7ea);
	border-radius: 50%;
	border-top-color: var(--primary, #0089ff);
	animation: eip-spin 0.8s linear infinite;
	margin-bottom: 12px;
}
@keyframes eip-spin { to { transform: rotate(360deg); } }

.eip-analysis-error {
	padding: 14px 18px;
	border-radius: var(--border-radius, 6px);
	background: var(--red-50, #fff5f5);
	border: 1px solid var(--red-200, #feb2b2);
	margin-bottom: 16px;
}
.eip-analysis-error p { margin: 6px 0 10px; font-size: 14px; }

/* ── Cards ── */
.eip-card {
	margin-bottom: 20px;
	border-radius: var(--border-radius, 6px);
	border: 1px solid var(--border-color, #d1d8dd);
	background: var(--card-bg, #fff);
	transition: border-color 0.2s, opacity 0.2s;
	overflow: hidden;
}
.eip-card-accepted { border-color: var(--green-400, #48bb78) !important; }
.eip-card-rejected { border-color: var(--red-400, #fc8181) !important; opacity: 0.72; }
.eip-card-deferred { opacity: 0.48; }
.eip-card-error    { border-color: var(--orange-400, #f6ad55) !important; }

.eip-card-header {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 12px 18px;
	border-bottom: 1px solid var(--border-color, #d1d8dd);
	flex-wrap: wrap;
	background: var(--subtle-fg, #fafbfc);
}
.eip-card-num {
	font-size: 12px;
	font-weight: 700;
	color: var(--text-muted);
	min-width: 20px;
}

/* ── Card body ── */
.eip-card-body { padding: 16px 18px; }

.eip-field { margin-bottom: 14px; }
.eip-field:last-child { margin-bottom: 0; }
.eip-field-label {
	font-size: 10px;
	font-weight: 700;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	color: var(--text-muted);
	margin-bottom: 4px;
}
.eip-field-value {
	font-size: 14px;
	color: var(--text-color, #36414c);
	line-height: 1.55;
}
.eip-list {
	margin: 2px 0 0;
	padding-left: 18px;
}
.eip-list li { margin-bottom: 4px; font-size: 14px; line-height: 1.5; }

/* ── Causal hypothesis ── */
.eip-causal-hypothesis { font-size: 14px; line-height: 1.75; }
.eip-ch-if   { color: var(--text-muted); font-style: italic; }
.eip-ch-then { display: flex; gap: 6px; }
.eip-ch-arrow { color: var(--primary, #0089ff); font-weight: 700; flex-shrink: 0; }

/* ── Verification plan grid ── */
.eip-vp {
	display: grid;
	grid-template-columns: 120px 1fr;
	gap: 4px 12px;
	font-size: 14px;
}
.eip-vp-label {
	color: var(--text-muted);
	font-size: 12px;
	align-self: start;
	padding-top: 1px;
}
.eip-dir { font-weight: 600; }

/* ── Reasoning section ── */
.eip-reasoning-toggle {
	cursor: pointer;
	display: inline-flex;
	align-items: center;
	gap: 4px;
	color: var(--primary, #0089ff);
	font-size: 13px;
	user-select: none;
	margin-top: 10px;
}
.eip-reasoning-toggle:hover { text-decoration: underline; }

.eip-reasoning-details {
	margin-top: 14px;
	padding-top: 14px;
	border-top: 1px solid var(--border-color, #d1d8dd);
}

.eip-dim-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.eip-dim-table td { padding: 4px 0; vertical-align: top; }
.eip-dim-table td:first-child {
	color: var(--text-muted);
	font-size: 12px;
	width: 155px;
	padding-right: 12px;
}

/* ── Card actions ── */
.eip-card-actions {
	padding: 12px 18px;
	border-top: 1px solid var(--border-color, #d1d8dd);
	display: flex;
	align-items: center;
	gap: 10px;
	flex-wrap: wrap;
	background: var(--subtle-fg, #fafbfc);
}
.eip-action-result {
	display: flex;
	align-items: center;
	gap: 10px;
	font-size: 14px;
	flex-wrap: wrap;
}
.eip-action-label         { font-weight: 600; }
.eip-action-label.accepted { color: var(--green-600, #276749); }
.eip-action-label.rejected  { color: var(--red-600, #c53030); }
.eip-action-label.deferred  { color: var(--text-muted); }
.eip-card-err-msg { font-size: 13px; color: var(--red-600, #c53030); }

.eip-reject-form { display: flex; flex-direction: column; gap: 8px; width: 100%; }
.eip-reject-form-btns { display: flex; gap: 8px; }

/* ── Summary banner ── */
.eip-summary {
	text-align: center;
	padding: 28px;
	border-radius: var(--border-radius, 6px);
	background: var(--control-bg, #f8f9fa);
	border: 1px solid var(--border-color, #d1d8dd);
	margin-top: 8px;
}
.eip-summary h5  { margin: 0 0 6px; font-size: 16px; }
.eip-summary p   { color: var(--text-muted); margin-bottom: 16px; font-size: 14px; }
`;

// ── Page entry point ──────────────────────────────────────────────────────────

frappe.pages['eip-decision-intelligence'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent:        wrapper,
		title:         __('EIP Decision Intelligence'),
		single_column: true,
	});
	new EIPDecisionPage(page, wrapper);
};

// ── Controller ────────────────────────────────────────────────────────────────

class EIPDecisionPage {

	constructor(page, wrapper) {
		this.page    = page;
		this.wrapper = wrapper;
		this.state   = this._initial_state();

		// Cached DOM references
		this.charter_field    = null;
		this.$analyse_btn     = null;
		this.$status_bar      = null;
		this.$recs_area       = null;
		this._timeout_guard   = null;

		this._inject_styles();
		this._build_layout();
		this._bind_events();
		this.render();
	}

	// ── Initialisation ────────────────────────────────────────────────────────

	_inject_styles() {
		if (document.getElementById(EIP_STYLE_ID)) return;
		$('<style>').attr('id', EIP_STYLE_ID).text(EIP_CSS).appendTo('head');
	}

	_build_layout() {
		const $wrap = $('<div class="eip-wrap">').appendTo(this.page.main);

		// Controls bar
		const $bar = $('<div class="eip-controls-bar">').appendTo($wrap);
		const $cw  = $('<div class="eip-charter-wrap">').appendTo($bar);

		this.charter_field = frappe.ui.form.make_control({
			df: {
				fieldtype: 'Link',
				fieldname: 'charter_name',
				label:     __('Lighthouse Workflow Charter'),
				options:   'Lighthouse Workflow Charter',
				placeholder: __('Select a Baseline Accepted charter…'),
				onchange:  () => this._on_charter_change(),
			},
			parent:       $cw[0],
			render_input: true,
		});
		this.charter_field.refresh();
		this.charter_field.set_query(() => ({
			filters: { approval_state: 'Baseline Accepted' },
		}));

		this.$analyse_btn = $(`<button class="btn btn-primary eip-analyse-btn">${__('Analyse')}</button>`)
			.prop('disabled', true)
			.appendTo($bar);

		// Status bar
		this.$status_bar = $('<div class="eip-status-bar">').appendTo($wrap);

		// Recommendations area
		this.$recs_area = $('<div class="eip-recs-area">').appendTo($wrap);
	}

	_bind_events() {
		this.$analyse_btn.on('click', () => this.analyse());

		// Single delegated handler for all card interactions
		this.$recs_area.on('click', '[data-action]', (e) => {
			e.preventDefault();
			const $el    = $(e.currentTarget);
			const action = $el.data('action');
			const idx    = parseInt($el.data('idx'), 10);
			this._dispatch(action, idx);
		});
	}

	// ── State ─────────────────────────────────────────────────────────────────

	_initial_state() {
		return {
			charter_name:   null,
			package:        null,
			cards:          null,
			is_analysing:   false,
			analysis_error: null,
		};
	}

	set_state(updates) {
		Object.assign(this.state, updates);
	}

	reset_analysis() {
		this.set_state({
			package:        null,
			cards:          null,
			is_analysing:   false,
			analysis_error: null,
		});
		this.render();
	}

	_init_cards(recommendations) {
		const cards = {};
		(recommendations || []).forEach((rec, idx) => {
			cards[idx] = {
				status:           EIP_STATUS.PENDING,
				rejection_reason: null,
				decision_record:  null,
				trace_record:     null,
				rejection_log:    null,
				error:            null,
				last_action:      null,
			};
		});
		return cards;
	}

	_is_all_actioned() {
		if (!this.state.cards) return false;
		return !Object.values(this.state.cards).some(
			c => c.status === EIP_STATUS.PENDING || c.status === EIP_STATUS.LOADING
		);
	}

	// ── Action dispatcher ─────────────────────────────────────────────────────

	_dispatch(action, idx) {
		const map = {
			'accept':           () => this.accept(idx),
			'show-reject':      () => this._show_reject_input(idx),
			'confirm-reject':   () => this.reject(idx),
			'cancel-reject':    () => this._hide_reject_input(idx),
			'defer':            () => this.defer(idx),
			'undo-defer':       () => this._undo_defer(idx),
			'retry-accept':     () => this.accept(idx),
			'retry-reject':     () => this._show_reject_input(idx),
			'retry-analysis':   () => this.analyse(),
			'open-dr':          () => {
				const dr = this.state.cards[idx] && this.state.cards[idx].decision_record;
				if (dr) frappe.set_route('Form', 'Decision Record', dr);
			},
			'toggle-reasoning': () => this._toggle_reasoning(idx),
			'new-analysis':     () => this.reset_analysis(),
		};
		if (map[action]) map[action]();
	}

	// ── API calls ─────────────────────────────────────────────────────────────

	analyse() {
		const charter_name = this.charter_field && this.charter_field.get_value();
		if (!charter_name) {
			frappe.show_alert({ message: __('Please select a charter first.'), indicator: 'orange' });
			return;
		}

		clearTimeout(this._timeout_guard);
		this.set_state({
			charter_name,
			package:        null,
			cards:          null,
			is_analysing:   true,
			analysis_error: null,
		});
		this.render();

		// Client-side guard — frappe.call does not expose a custom timeout setting
		this._timeout_guard = setTimeout(() => {
			if (!this.state.is_analysing) return;
			this.set_state({ is_analysing: false, analysis_error: 'timeout' });
			this.render();
		}, EIP_ANALYSIS_TIMEOUT_MS);

		frappe.call({
			method: EIP_API.GET,
			args:   { charter_name },
			freeze: false,
			callback: (r) => {
				clearTimeout(this._timeout_guard);
				this.render_recommendations(r.message);
			},
			error: (r) => {
				clearTimeout(this._timeout_guard);
				this.set_state({
					is_analysing:   false,
					analysis_error: this._extract_error(r),
				});
				this.render();
			},
		});
	}

	accept(idx) {
		this._set_card_loading(idx, 'accept');

		frappe.call({
			method: EIP_API.ACCEPT,
			freeze: false,
			args: {
				charter_name:        this.state.charter_name,
				recommendation_data: JSON.stringify(this._build_payload(idx)),
			},
			callback: (r) => {
				Object.assign(this.state.cards[idx], {
					status:          EIP_STATUS.ACCEPTED,
					decision_record: r.message.decision_record,
					trace_record:    r.message.trace_record,
				});
				this._refresh_card(idx);
				this.render_summary();
				frappe.show_alert({ message: __('Decision Record created.'), indicator: 'green' });
			},
			error: (r) => {
				Object.assign(this.state.cards[idx], {
					status:      EIP_STATUS.ERROR,
					error:       this._extract_error(r),
					last_action: 'accept',
				});
				this._refresh_card(idx);
			},
		});
	}

	reject(idx) {
		const $input = this._$card(idx).find('.eip-reject-reason');
		const reason = ($input.val() || '').trim();

		if (!reason) {
			frappe.show_alert({ message: __('Please enter a rejection reason.'), indicator: 'orange' });
			$input.focus();
			return;
		}

		this._set_card_loading(idx, 'reject');

		frappe.call({
			method: EIP_API.REJECT,
			freeze: false,
			args: {
				charter_name:        this.state.charter_name,
				recommendation_data: JSON.stringify(this._build_payload(idx)),
				reason,
			},
			callback: (r) => {
				Object.assign(this.state.cards[idx], {
					status:           EIP_STATUS.REJECTED,
					rejection_log:    r.message.rejection_log,
					rejection_reason: reason,
				});
				this._refresh_card(idx);
				this.render_summary();
			},
			error: (r) => {
				Object.assign(this.state.cards[idx], {
					status:      EIP_STATUS.ERROR,
					error:       this._extract_error(r),
					last_action: 'reject',
				});
				this._refresh_card(idx);
			},
		});
	}

	defer(idx) {
		this.state.cards[idx].status = EIP_STATUS.DEFERRED;
		this._refresh_card(idx);
		this.render_summary();
	}

	// ── Client-only card actions ──────────────────────────────────────────────

	_undo_defer(idx) {
		this.state.cards[idx].status = EIP_STATUS.PENDING;
		this._refresh_card(idx);
		this.$recs_area.find('.eip-summary').remove();
	}

	_show_reject_input(idx) {
		this._$actions(idx).html(`
			<div class="eip-reject-form">
				<input type="text" class="form-control eip-reject-reason"
				       placeholder="${__('Reason for rejection…')}" />
				<div class="eip-reject-form-btns">
					<button class="btn btn-sm btn-danger"
					        data-action="confirm-reject" data-idx="${idx}">
						${__('Confirm Rejection')}
					</button>
					<button class="btn btn-sm btn-secondary"
					        data-action="cancel-reject" data-idx="${idx}">
						${__('Cancel')}
					</button>
				</div>
			</div>
		`);
		this._$actions(idx).find('.eip-reject-reason').focus();
	}

	_hide_reject_input(idx) {
		this._$actions(idx).html(this._pending_buttons_html(idx));
	}

	_toggle_reasoning(idx) {
		const $det = this._$card(idx).find('.eip-reasoning-details');
		const open = $det.is(':visible');
		$det.slideToggle(150);
		this._$card(idx).find('.eip-tog-arrow').text(open ? '▶' : '▼');
	}

	_set_card_loading(idx, action) {
		Object.assign(this.state.cards[idx], { status: EIP_STATUS.LOADING, last_action: action });
		this._$actions(idx).html(
			`<span class="text-muted"><span class="spinner-border spinner-border-sm"></span> ${__('Processing…')}</span>`
		);
	}

	// ── Rendering ─────────────────────────────────────────────────────────────

	render() {
		this.render_controls();
		this.render_status_bar();

		if (this.state.is_analysing) { this.render_loading();      return; }
		if (this.state.analysis_error) { this.render_error();      return; }
		if (!this.state.package)       { this.render_empty_state(); return; }

		this.render_cards();
		this.render_summary();
	}

	render_controls() {
		const has_charter = !!(this.charter_field && this.charter_field.get_value());
		const busy        = this.state.is_analysing;
		this.$analyse_btn.prop('disabled', !has_charter || busy).html(
			busy
				? `<span class="spinner-border spinner-border-sm"></span> ${__('Analysing…')}`
				: __('Analyse')
		);
	}

	render_status_bar() {
		this.$status_bar.empty();
		const pkg = this.state.package;
		if (!pkg) return;

		const color = pkg.fallback_used ? 'orange' : 'blue';
		this.$status_bar.append(
			`<span class="indicator-pill ${color} no-indicator">${this._esc(pkg.model_identifier)}</span>`
		);
		if (pkg.fallback_used) {
			this.$status_bar.append(
				`<span class="indicator-pill orange">⚠ ${__('Deterministic fallback')}</span>`
			);
		}
		const ts = (pkg.execution_timestamp || '').split('T')[1];
		if (ts) {
			this.$status_bar.append(
				`<span class="eip-ts">${__('Analysed at')} ${this._esc(ts.substring(0, 5))}</span>`
			);
		}
	}

	render_loading() {
		this.$recs_area.html(`
			<div class="eip-loading-area">
				<div class="eip-spinner"></div>
				<p>${__('Generating recommendations… This may take up to 60 seconds.')}</p>
			</div>
		`);
	}

	render_error() {
		const msg = this._error_message_for(this.state.analysis_error);
		this.$recs_area.html(`
			<div class="eip-analysis-error">
				<strong>${__('Analysis failed')}</strong>
				<p>${this._esc(msg)}</p>
				<button class="btn btn-sm btn-secondary" data-action="retry-analysis">
					${__('Try Again')}
				</button>
			</div>
		`);
	}

	render_empty_state() {
		this.$recs_area.html(`
			<div class="eip-empty-state">
				<div class="eip-empty-icon">🔍</div>
				<h5>${__('Select a charter and click Analyse to begin.')}</h5>
				<p>${__('Only Baseline Accepted charters are available for analysis.')}</p>
			</div>
		`);
	}

	// Transport-agnostic entry point — independent of whether package came from
	// a synchronous HTTP response, a background job, or a mock (Slice 2 compatible)
	render_recommendations(pkg) {
		this.set_state({
			package:      pkg,
			cards:        this._init_cards(pkg.recommendations),
			is_analysing: false,
		});
		this.render();
	}

	render_cards() {
		this.$recs_area.empty();
		const recs = this.state.package && this.state.package.recommendations;

		if (!recs || !recs.length) {
			this.$recs_area.html(`
				<div class="eip-empty-state">
					<div class="eip-empty-icon">📋</div>
					<h5>${__('No recommendations generated.')}</h5>
					<p>${__('The charter may have insufficient active decision signals. Add open decisions, dependencies, or KPIs and try again.')}</p>
				</div>
			`);
			return;
		}

		recs.forEach((rec, idx) => this.$recs_area.append(this._build_card(rec, idx)));
	}

	render_summary() {
		let $sum = this.$recs_area.find('.eip-summary');

		if (!this._is_all_actioned()) {
			$sum.remove();
			return;
		}

		const totals = Object.values(this.state.cards).reduce((acc, c) => {
			acc[c.status] = (acc[c.status] || 0) + 1;
			return acc;
		}, {});

		const accepted = totals[EIP_STATUS.ACCEPTED] || 0;
		const rejected = totals[EIP_STATUS.REJECTED] || 0;
		const deferred = totals[EIP_STATUS.DEFERRED] || 0;

		if (!$sum.length) $sum = $('<div class="eip-summary">').appendTo(this.$recs_area);

		$sum.html(`
			<h5>${__('Analysis Complete')}</h5>
			<p>${accepted} ${__('accepted')} · ${rejected} ${__('rejected')} · ${deferred} ${__('deferred')}</p>
			<button class="btn btn-primary btn-sm" data-action="new-analysis">
				${__('New Analysis')}
			</button>
		`);
	}

	// ── Card construction ─────────────────────────────────────────────────────

	_build_card(rec, idx) {
		const cc = EIP_CONF_COLOR[rec.confidence_state && rec.confidence_state.band] || 'gray';
		const lc = EIP_CLASS_COLOR[rec.recommendation_class] || 'gray';

		const $card = $(`
			<div class="eip-card frappe-card" data-idx="${idx}">
				<div class="eip-card-header">
					<span class="eip-card-num">#${idx + 1}</span>
					<span class="indicator-pill no-indicator ${lc}">
						${this._esc(rec.recommendation_class)}
					</span>
					<span class="indicator-pill ${cc}">
						${this._esc((rec.confidence_state || {}).band)} ${__('Confidence')}
					</span>
				</div>
				<div class="eip-card-body"></div>
				<div class="eip-card-actions"></div>
			</div>
		`);

		this._populate_body($card.find('.eip-card-body'), rec, idx);
		$card.find('.eip-card-actions').html(this._pending_buttons_html(idx));
		return $card;
	}

	_populate_body($body, rec, idx) {
		const cs = rec.confidence_state || {};
		const vp = rec.verification_plan || {};

		$body
			.append(this._field(__('Objective'),
				`<div class="eip-field-value">${this._esc(rec.objective_served)}</div>`))

			.append(this._field(__('Causal Hypothesis'),
				this._format_hypothesis(rec.causal_hypothesis)))

			.append(this._field(
				`${__('Assumptions')} <span class="text-muted">(${(rec.assumptions || []).length})</span>`,
				this._list(rec.assumptions)))

			.append(this._field(
				`${__('Trade-offs')} <span class="text-muted">(${(rec.trade_offs || []).length})</span>`,
				this._list(rec.trade_offs)))

			.append(this._field(__('Risk Exposure'),
				`<div class="eip-field-value">${this._esc(rec.risk_exposure)}</div>`))

			.append(this._field(__('Dependency Implications'),
				`<div class="eip-field-value">${this._esc(rec.dependency_implications)}</div>`))

			.append(this._field(__('Verification Plan'), this._format_vp(vp)))

			.append(this._field(__('Owner & Review Point'),
				`<div class="eip-field-value">${this._esc(rec.owner_and_review_point)}</div>`));

		// Reasoning toggle + collapsible details
		$body.append(`
			<div class="eip-reasoning-toggle" data-action="toggle-reasoning" data-idx="${idx}">
				<span class="eip-tog-arrow">▶</span>&nbsp;${__('Reasoning Details')}
			</div>
		`);
		$body.append(this._build_reasoning(rec));
	}

	_build_reasoning(rec) {
		const cs  = rec.confidence_state || {};
		const pkg = this.state.package || {};
		const $d  = $('<div class="eip-reasoning-details">').hide();

		$d.append(this._field(__('Confidence Rationale'),
			`<div class="eip-field-value">${this._esc(cs.rationale)}</div>`));

		const dims = cs.dimensions || {};
		const rows = Object.entries(dims)
			.map(([k, v]) => `<tr>
				<td>${this._esc(this._fmt_key(k))}</td>
				<td>${this._esc(v)}</td>
			</tr>`)
			.join('');

		if (rows) {
			$d.append(this._field(__('Evidence Dimensions'),
				`<table class="eip-dim-table"><tbody>${rows}</tbody></table>`));
		}

		$d.append(`
			<div class="eip-field">
				<span class="text-muted" style="font-size:12px;">
					${__('Model')}: ${this._esc(pkg.model_identifier)}
					&nbsp;&nbsp;|&nbsp;&nbsp;
					${__('Fallback')}: ${pkg.fallback_used ? __('Yes') : __('No')}
				</span>
			</div>
		`);

		return $d;
	}

	// ── Card action HTML generators ────────────────────────────────────────────

	_actions_html(idx) {
		const cs = this.state.cards[idx];
		if (!cs) return '';

		switch (cs.status) {
			case EIP_STATUS.PENDING:
				return this._pending_buttons_html(idx);

			case EIP_STATUS.LOADING:
				return `<span class="text-muted">
					<span class="spinner-border spinner-border-sm"></span> ${__('Processing…')}
				</span>`;

			case EIP_STATUS.ACCEPTED:
				return `<div class="eip-action-result">
					<span class="eip-action-label accepted">✓ ${__('Accepted')}</span>
					<a href="#" class="btn btn-xs btn-secondary"
					   data-action="open-dr" data-idx="${idx}">
						${__('View Decision Record →')}
					</a>
				</div>`;

			case EIP_STATUS.REJECTED:
				return `<div class="eip-action-result">
					<span class="eip-action-label rejected">✗ ${__('Rejected')}</span>
					<span class="text-muted" style="font-size:13px;">— ${this._esc(cs.rejection_reason)}</span>
				</div>`;

			case EIP_STATUS.DEFERRED:
				return `<div class="eip-action-result">
					<span class="eip-action-label deferred">◷ ${__('Deferred')}</span>
					<a href="#" class="text-muted" style="font-size:13px;"
					   data-action="undo-defer" data-idx="${idx}">${__('Undo')}</a>
				</div>`;

			case EIP_STATUS.ERROR: {
				const retry = cs.last_action === 'accept' ? 'retry-accept' : 'retry-reject';
				return `<div class="eip-action-result" style="flex-wrap:wrap;gap:8px;">
					<span class="eip-card-err-msg">⚠ ${this._esc(cs.error)}</span>
					<button class="btn btn-sm btn-secondary"
					        data-action="${retry}" data-idx="${idx}">
						${__('Retry')}
					</button>
				</div>`;
			}

			default:
				return this._pending_buttons_html(idx);
		}
	}

	_pending_buttons_html(idx) {
		return `
			<button class="btn btn-sm btn-primary"   data-action="accept"      data-idx="${idx}">${__('Accept')}</button>
			<button class="btn btn-sm btn-danger"    data-action="show-reject" data-idx="${idx}">${__('Reject')}</button>
			<button class="btn btn-sm btn-secondary" data-action="defer"       data-idx="${idx}">${__('Defer')}</button>
		`;
	}

	// Refresh only the actions area + card border after a state change
	_refresh_card(idx) {
		this._$actions(idx).html(this._actions_html(idx));
		const status = this.state.cards[idx] && this.state.cards[idx].status;
		const $card  = this._$card(idx);
		$card.removeClass('eip-card-accepted eip-card-rejected eip-card-deferred eip-card-error');
		if (status && status !== EIP_STATUS.PENDING && status !== EIP_STATUS.LOADING) {
			$card.addClass(`eip-card-${status}`);
		}
	}

	// ── DOM helpers ────────────────────────────────────────────────────────────

	_field(label, content) {
		const $f = $(`<div class="eip-field"><div class="eip-field-label">${label}</div></div>`);
		$f.append(content);
		return $f;
	}

	_list(items) {
		if (!items || !items.length) return $('<div class="eip-field-value text-muted">—</div>');
		return $(`<ul class="eip-list">${items.map(i => `<li>${this._esc(i)}</li>`).join('')}</ul>`);
	}

	_format_hypothesis(text) {
		if (!text) return $('<div>');
		const $d = $('<div class="eip-causal-hypothesis">');
		text.split('→').map(s => s.trim()).forEach((part, i) => {
			if (i === 0) {
				$d.append(`<div class="eip-ch-if">${this._esc(part)}</div>`);
			} else {
				$d.append(`<div class="eip-ch-then">
					<span class="eip-ch-arrow">→</span>&nbsp;${this._esc(part)}
				</div>`);
			}
		});
		return $d;
	}

	_format_vp(vp) {
		const arrow = EIP_DIR_ARROW[vp.expected_kpi_direction] || '';
		return $(`
			<div class="eip-vp">
				<span class="eip-vp-label">${__('Baseline')}</span>
				<span>${this._esc(vp.baseline)}</span>
				<span class="eip-vp-label">${__('Direction')}</span>
				<span class="eip-dir">${arrow} ${this._esc(vp.expected_kpi_direction)}</span>
				<span class="eip-vp-label">${__('Window')}</span>
				<span>${this._esc(vp.review_window)}</span>
				<span class="eip-vp-label">${__('Criteria')}</span>
				<span>${this._esc(vp.acceptance_criteria)}</span>
			</div>
		`);
	}

	_build_payload(idx) {
		const rec = this.state.package.recommendations[idx];
		const pkg = this.state.package;
		return Object.assign({}, rec, {
			model_identifier:    pkg.model_identifier,
			fallback_used:       pkg.fallback_used,
			execution_timestamp: pkg.execution_timestamp,
			context_snapshot:    pkg.context_snapshot,
		});
	}

	_fmt_key(key) {
		return (key || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
	}

	_esc(s) {
		return frappe.utils.escape_html(s == null ? '' : String(s));
	}

	_$card(idx)    { return this.$recs_area.find(`.eip-card[data-idx="${idx}"]`); }
	_$actions(idx) { return this._$card(idx).find('.eip-card-actions'); }

	_on_charter_change() {
		const val = this.charter_field ? this.charter_field.get_value() : null;
		const changed = val !== this.state.charter_name;
		this.set_state({ charter_name: val || null });
		if (changed && this.state.package) this.reset_analysis();
		this.render_controls();
	}

	_error_message_for(error) {
		if (error === 'timeout') {
			return __('Analysis timed out. The AI model may be under load. Try again later.');
		}
		if (!error || typeof error !== 'string') {
			return __('An unexpected error occurred. Please try again.');
		}
		if (/permission/i.test(error))      return __('You do not have permission to analyse this charter.');
		if (/doesnot|not found/i.test(error)) return __('Charter not found. Please select a valid charter.');
		if (/baseline accepted/i.test(error)) return __('This charter is not in Baseline Accepted state. Check the charter record and try again.');
		return error;
	}

	_extract_error(r) {
		if (!r) return __('Unknown error');
		const raw = r._server_messages;
		if (raw) {
			try {
				const parsed = JSON.parse(raw);
				const first  = Array.isArray(parsed) ? JSON.parse(parsed[0]) : parsed;
				return first.message || raw;
			} catch (_) {
				return raw;
			}
		}
		return r.message || r.exc_type || __('Unknown error');
	}
}
