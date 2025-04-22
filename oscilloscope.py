import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import traceback
import time

# --- Default Parameters & Ranges ---
DEFAULT_AMP = 1.0
DEFAULT_X_FACTOR = 2.0
DEFAULT_PHI = 0
DEFAULT_TQT_FACTOR = 1.0
DEFAULT_TQN_FACTOR = 0.25
DEFAULT_PHI_UNIT = 'deg'
DEFAULT_INPUT_FUNC = 'sin'
DEFAULT_BASE_FONT_SIZE = 11

AMP_RANGE = (0, 10.0)
X_FACTOR_RANGE = (0.1, 10.0)
PHI_RANGE = (-360.0, 360.0); PHI_RAD_RANGE = (-2 * np.pi, 2 * np.pi)
T_FACTOR_RANGE = (0.05, 5.0)
FONT_SIZES = [10, 11, 12, 14, 16, 18, 20]

# --- Global references ---
root = None; style = None
amp_slider = None; omega_slider = None; phi_slider = None
amp_var = None; omega_var = None; phi_var = None; phi_unit_var = None; phi_label_var = None
input_func_var = None
input_title_var = None
tqt_factor_slider = None; tqn_factor_slider = None
tqt_factor_var = None; tqn_factor_var = None
theme_var = None; theme_combo = None
font_size_combo = None; font_size_var = None
canvas = None; fig = None; ax = None
line_input = None; line_sweep = None;
is_plot_initialized = False
quick_set_buttons = []; button_wrapper_frame = None;
redraw_timer_id = None
global_entry_widgets = [] # Keep list for Entry workaround

# --- Global Font Objects REMOVED ---
# Reverting to style-based font control

# --- Theme Definitions ---
THEMES = {
    "Dark Scope": {'tk_bg': '#2E2E2E', 'tk_fg': 'white', 'ttk_theme': 'clam', 'fig_bg': 'black', 'ax_bg': 'black', 'text': 'white', 'grid_major': '#888888', 'grid_minor': '#555555', 'spine': '#888888', 'trace_input': 'cyan', 'trace_sweep': '#FFDD00', 'trace_yt_fwd': 'cyan', 'trace_yt_ret': '#FF8888', 'button_bg': '#4F4F4F', 'button_active_bg': '#6A6A6A'},
    "Light": {'tk_bg': '#F0F0F0', 'tk_fg': 'black', 'ttk_theme': 'vista', 'fig_bg': 'white', 'ax_bg': 'white', 'text': 'black', 'grid_major': '#D0D0D0', 'grid_minor': '#EAEAEA', 'spine': 'black', 'trace_input': 'blue', 'trace_sweep': 'orange', 'trace_yt_fwd': 'blue', 'trace_yt_ret': 'red', 'button_bg': '#E1E1E1', 'button_active_bg': '#CFCFCF'},
    "Blueprint": {'tk_bg': '#D0E0F0', 'tk_fg': '#1A2E40', 'ttk_theme': 'alt', 'fig_bg': '#2A4D69', 'ax_bg': '#4B86B4', 'text': '#FFFFFF', 'grid_major': '#ADCBE3', 'grid_minor': '#63ACE5', 'spine': '#ADCBE3', 'trace_input': '#FFFFB3', 'trace_sweep': '#FFD633', 'trace_yt_fwd': '#FFFFB3', 'trace_yt_ret': '#FF8888', 'button_bg': '#87CEEB', 'button_active_bg': '#A1DFFF'}
}
DEFAULT_THEME = "Dark Scope"

# --- Global Color Variables ---
bg_color=None; text_color=None; grid_major_color=None; grid_minor_color=None; spine_color=None
trace_color_input=None; trace_color_sweep=None; trace_color_yt_fwd=None; trace_color_yt_ret = None;
tk_bg_color=None; tk_fg_color=None; fig_bg_color=None; ax_bg_color=None; button_bg_color=None; button_active_bg_color=None

# --- Helper Functions ---
def get_phi_range(): return PHI_RANGE if phi_unit_var.get() == 'deg' else PHI_RAD_RANGE
def get_phi_format(): return "{:.1f}" if phi_unit_var.get() == 'deg' else "{:.3f}"
def get_xfactor_range(): return X_FACTOR_RANGE
def get_amp_range(): return AMP_RANGE
def get_t_factor_range(): return T_FACTOR_RANGE

def create_entry_handler(entry_var, slider, slider_range_provider, format_spec_provider):
    # --- THIS FUNCTION HAS THE CORRECTED SYNTAX ---
    def handler(event=None):
        global root
        value_str = entry_var.get() # Get value_str outside try for use in except
        try:
            # Attempt to convert and validate
            value=float(value_str)
            current_range=slider_range_provider(); format_spec=format_spec_provider()
            min_val,max_val=current_range; validated_value=max(min_val,min(value,max_val))
            current_slider_val=slider.get()

            # Update slider if value is valid and different
            if not np.isclose(validated_value, current_slider_val):
                 slider.set(validated_value)
            else:
                 # Ensure formatting is correct even if value is the same
                 entry_var.set(format_spec.format(validated_value))

        except ValueError:
            # Handle case where input wasn't a valid float
            print(f"Invalid input: '{value_str}'. Please enter a number.")
            # Attempt to revert entry text to slider's current value
            # CORRECTED Structure: try/except are indented on new lines
            try:
                 format_spec = format_spec_provider()
                 current_slider_val = slider.get()
                 entry_var.set(format_spec.format(current_slider_val))
            except Exception as e:
                 print(f"Error reverting entry: {e}")
            # End Correction
            # Always return after handling ValueError or its nested exception
            return

        except Exception as e:
            # Catch any other unexpected errors during validation/update
            print(f"Error handling entry update: {e}"); traceback.print_exc()
            # Stop processing this event
            return
    return handler

def update_input_title(*args):
    """Updates the title label based on sin/cos selection."""
    global input_func_var, input_title_var, is_plot_initialized
    if input_func_var and input_title_var:
        func_name = input_func_var.get()  # 'sin' or 'cos'
        input_title_var.set(f"Input Signal: y = A{func_name}(wt+phi)")
    is_plot_initialized = False
    update_plot()


def update_plot(*args):
    """
    Reads controls, calculates signals, and updates the Matplotlib plots.
    (Reorganized Version)
    """
    # Declare necessary globals (required for standalone function)
    global canvas, fig, ax, is_plot_initialized
    global amp_slider, omega_slider, phi_slider, tqt_factor_slider, tqn_factor_slider, font_size_combo
    global amp_var, omega_var, phi_var, tqt_factor_var, tqn_factor_var, phi_unit_var, input_func_var, font_size_var
    global line_input, line_sweep
    global ax_bg_color, text_color, grid_major_color, grid_minor_color, spine_color
    global trace_color_input, trace_color_sweep, trace_color_yt_fwd, trace_color_yt_ret

    # --- 1. Readiness Check ---
    widgets_and_vars_ready = all([
        canvas, fig,
        amp_slider, omega_slider, phi_slider, tqt_factor_slider, tqn_factor_slider, font_size_combo,
        amp_var, omega_var, phi_var, tqt_factor_var, tqn_factor_var, phi_unit_var, input_func_var, font_size_var,
        # Also check colors needed early
        ax_bg_color, text_color, grid_major_color, grid_minor_color, spine_color,
        trace_color_input, trace_color_sweep, trace_color_yt_fwd, trace_color_yt_ret
    ])
    # Explicitly check the axes array separately
    axes_ready = ax is not None and len(ax) == 3 # Assuming ax is assigned elsewhere

    if not widgets_and_vars_ready or not axes_ready:
        # print("Plot update skipped: Components not ready.")
        return

    try:
        # --- 2. Get Parameters & Calculate Font Sizes ---
        try:
            base_font_size = int(font_size_var.get())
        except (ValueError, tk.TclError):
            base_font_size = DEFAULT_BASE_FONT_SIZE
            if font_size_var: font_size_var.set(str(DEFAULT_BASE_FONT_SIZE)) # Prevent error loop

        plot_title_fontsize = base_font_size + 3
        plot_label_fontsize = base_font_size + 1
        plot_legend_fontsize = base_font_size - 1
        plot_text_fontsize = base_font_size - 2
        tick_label_fontsize = base_font_size - 1

        A = amp_slider.get()
        x_factor = omega_slider.get()
        phi_value = phi_slider.get()
        current_phi_unit = phi_unit_var.get()
        tqt_factor = tqt_factor_slider.get()
        tqn_factor = tqn_factor_slider.get()
        selected_func = input_func_var.get()

        # --- 3. Update Tkinter Variable Displays ---
        amp_var.set(f"{A:.2f}")
        omega_var.set(f"{x_factor:.2f}")
        phi_format_spec = get_phi_format() # Assumes get_phi_format depends on phi_unit_var
        phi_var.set(phi_format_spec.format(phi_value))
        tqt_factor_var.set(f"{tqt_factor:.2f}")
        tqn_factor_var.set(f"{tqn_factor:.2f}")

        # --- 4. Core Signal Calculations ---
        omega = x_factor * np.pi
        phi_rad = np.deg2rad(phi_value) if current_phi_unit == 'deg' else phi_value
        phi_display_deg = phi_value if current_phi_unit == 'deg' else np.rad2deg(phi_value)

        x_factor_safe = max(x_factor, 1e-6)
        Ty = 2.0 / x_factor_safe # Period of input signal

        Tqt = max(0.001, tqt_factor * Ty)
        Tqn = max(0.001, tqn_factor * Ty)
        T_total_sweep = Tqt + Tqn

        # Determine time range and points
        total_time = max(0.1, 3 * T_total_sweep, 5 * Ty, 1.5 * Tqt) # Ensure enough time
        points = 1000 # Use a reasonable number of points
        t = np.linspace(0, total_time, points, endpoint=False)

        # Calculate Input Signal y(t)
        if selected_func == 'cos':
            y = A * np.cos(omega * t + phi_rad)
        else: # Default to sin
            y = A * np.sin(omega * t + phi_rad)

        # Calculate Horizontal Sweep Signal x(t) (Normalized 0 to 1)
        x_sweep_signal = np.zeros_like(t)
        t_cycle = t % T_total_sweep
        forward_mask_sweep = t_cycle < Tqt
        if Tqt > 1e-9: x_sweep_signal[forward_mask_sweep] = t_cycle[forward_mask_sweep] / Tqt
        return_mask_sweep = ~forward_mask_sweep
        if Tqn > 1e-9:
            time_in_return = t_cycle[return_mask_sweep] - Tqt
            x_sweep_signal[return_mask_sweep] = 1.0 - (time_in_return / Tqn)
        else:
            x_sweep_signal[return_mask_sweep] = 0.0
        x_sweep_signal = np.clip(x_sweep_signal, 0, 1)

        # --- 5. Prepare Plot Metadata ---
        y_lim_val = max(abs(A) * 1.1, 0.5)
        input_legend_label = (f'A = {A:.2f}, x = {x_factor:.2f}\n'
                              f'ω = {omega:.2f} rad/s\n'
                              f'φ = {phi_display_deg:.1f}°\n'
                              f'func = {selected_func}')
        sweep_title_text = f'2. Horiz. Sweep (Tqt={Tqt:.3f}s, Tqn={Tqn:.3f}s)'
        scope_title_text = f'3. Oscilloscope (Y vs Sweep)'
        input_title_text = '1. Input Signal'

        # --- 6. Plotting ---
        ax1, ax2, ax3 = ax # Unpack axes

        # Always clear scope axes as it's fully replotted
        ax3.clear()

        # Initialize line objects if first time
        if not is_plot_initialized:
            ax1.clear()
            ax2.clear()
            line_input, = ax1.plot(t, y, color=trace_color_input) # Label set later
            line_sweep, = ax2.plot(t, x_sweep_signal, color=trace_color_sweep)
            is_plot_initialized = True
        # Check if line objects exist before using them (safety check)
        elif line_input is None or line_sweep is None:
             print("Error: Plot lines not initialized despite is_plot_initialized=True. Re-initializing.")
             is_plot_initialized = False # Force re-init next time
             # Could call the function again or just return to avoid deeper errors
             return

        # --- 6a. Update Line Data (Axes 1 & 2) ---
        line_input.set_data(t, y)
        line_input.set_label(input_legend_label) # Update label text
        line_sweep.set_data(t, x_sweep_signal)

        # --- 6b. Apply Styling and Configuration (All Axes - runs every time for theme/font changes) ---
        for i, ax_i in enumerate(ax):
            ax_i.set_facecolor(ax_bg_color)
            ax_i.grid(True, which='major', axis='both', linestyle='-', linewidth='0.6', color=grid_major_color)
            ax_i.grid(True, which='minor', axis='both', linestyle=':', linewidth='0.4', color=grid_minor_color)
            ax_i.tick_params(axis='both', colors=text_color, labelsize=tick_label_fontsize, which='both')
            for spine in ax_i.spines.values():
                spine.set_edgecolor(spine_color)
            # Ensure text elements have the correct color
            if ax_i.title: ax_i.title.set_color(text_color)
            if ax_i.xaxis.label: ax_i.xaxis.label.set_color(text_color)
            if ax_i.yaxis.label: ax_i.yaxis.label.set_color(text_color)

        # Axis 1: Input Signal
        ax1.set_title(input_title_text, fontsize=plot_title_fontsize, color=text_color)
        ax1.set_xlabel('Time (s)', fontsize=plot_label_fontsize, color=text_color)
        ax1.set_ylabel('Input Signal', fontsize=plot_label_fontsize, color=text_color)
        ax1.set_xlim(0, total_time)
        ax1.set_ylim(-y_lim_val, y_lim_val)
        major_step_y0 = max(y_lim_val / 4, 1e-6); minor_step_y0 = major_step_y0 / 5
        ax1.yaxis.set_major_locator(MultipleLocator(major_step_y0))
        ax1.yaxis.set_minor_locator(MultipleLocator(minor_step_y0))
        ax1.xaxis.set_minor_locator(AutoMinorLocator())
        # Update/create legend for Axis 1
        ax1.legend(fontsize=plot_legend_fontsize, loc='center left', bbox_to_anchor=(1, 0.5),
                   facecolor=ax_bg_color, edgecolor=grid_major_color, labelcolor=text_color)

        # Axis 2: Sweep Signal
        ax2.set_title(sweep_title_text, fontsize=plot_title_fontsize, color=text_color)
        ax2.set_xlabel('Time (s)', fontsize=plot_label_fontsize, color=text_color)
        ax2.set_ylabel('Norm. Horiz. Pos.', fontsize=plot_label_fontsize, color=text_color)
        ax2.set_xlim(0, total_time)
        ax2.set_ylim(-0.1, 1.1)
        ax2.xaxis.set_minor_locator(AutoMinorLocator())
        ax2.yaxis.set_major_locator(MultipleLocator(0.2))
        ax2.yaxis.set_minor_locator(MultipleLocator(0.05))
        # Add text annotations to Axis 2
        for txt in ax2.texts: txt.remove() # Clear previous text
        if total_time > 0 and T_total_sweep > 0 and Tqt > 1e-9 and Tqn > 1e-9:
            mid_fwd = Tqt / 2
            mid_ret = Tqt + Tqn / 2
            text_bg = list(plt.cm.colors.to_rgba(ax_bg_color))
            text_bg[3] = 0.5 # Alpha
            text_bg = tuple(text_bg)
            if mid_fwd < total_time: ax2.text(mid_fwd, 0.55, 'Fwd\nSweep', ha='center', va='bottom', fontsize=plot_text_fontsize, color=text_color, backgroundcolor=text_bg)
            if mid_ret < total_time: ax2.text(mid_ret, 0.45, 'Return\nSweep', ha='center', va='top', fontsize=plot_text_fontsize, color=text_color, backgroundcolor=text_bg)


        # Axis 3: Oscilloscope Screen (already cleared, needs full setup)
        ax3.set_title(scope_title_text, fontsize=plot_title_fontsize, color=text_color)
        ax3.set_xlabel('Normalized Sweep Position', fontsize=plot_label_fontsize, color=text_color)
        ax3.set_ylabel('Output Signal y(t)', fontsize=plot_label_fontsize, color=text_color)
        ax3.set_xlim(-0.05, 1.05)
        ax3.set_ylim(-y_lim_val, y_lim_val)
        major_step_y2 = max(y_lim_val / 4, 1e-6); minor_step_y2 = major_step_y2 / 5
        ax3.yaxis.set_major_locator(MultipleLocator(major_step_y2))
        ax3.yaxis.set_minor_locator(MultipleLocator(minor_step_y2))
        ax3.xaxis.set_major_locator(MultipleLocator(0.2))
        ax3.xaxis.set_minor_locator(MultipleLocator(0.05))

        # --- 6c. Plot Data Segments (Axis 3) ---
        num_cycles_to_plot = int(np.ceil(total_time / T_total_sweep)) if T_total_sweep > 1e-9 else 1
        first_tqt_plot = True; first_tqn_plot = True
        for k in range(num_cycles_to_plot):
            t_start = k * T_total_sweep
            t_mid = t_start + Tqt
            t_end = (k + 1) * T_total_sweep
            idx_tqt = (t >= t_start) & (t < t_mid) # Use < t_mid?
            idx_tqn = (t >= t_mid) & (t < t_end)

            if np.any(idx_tqt):
                label = 'Forward (Tqt)' if first_tqt_plot else ""
                ax3.plot(x_sweep_signal[idx_tqt], y[idx_tqt], linestyle='-', color=trace_color_yt_fwd, label=label)
                first_tqt_plot = False
            if np.any(idx_tqn):
                label = 'Return (Tqn)' if first_tqn_plot else ""
                ax3.plot(x_sweep_signal[idx_tqn], y[idx_tqn], linestyle='--', color=trace_color_yt_ret, label=label)
                first_tqn_plot = False

        # Add legend to Axis 3 if traces were plotted
        if not first_tqt_plot or not first_tqn_plot:
            ax3.legend(fontsize=plot_legend_fontsize, loc='center left', bbox_to_anchor=(1, 0.5),
                       facecolor=ax_bg_color, edgecolor=grid_major_color, labelcolor=text_color)

        # --- 7. Final Adjustments & Redraw ---
        try:
            fig.tight_layout(rect=[0, 0.02, 0.92, 0.95]) # Adjust rect as needed [left, bottom, right, top]
        except ValueError as e:
            print(f"Warning: tight_layout failed: {e}. Plot might overlap.")
            # Consider fig.subplots_adjust as fallback if necessary

        canvas.draw()

    except Exception as e:
        print(f"Error during plot update: {e}")
        traceback.print_exc()

# --- Other Functions ---
def update_phase_unit():
    global phi_slider, phi_var, phi_unit_var, phi_label_var, is_plot_initialized
    if not all([phi_slider, phi_var, phi_unit_var, phi_label_var]): print("Phase widgets not ready..."); return
    try: current_unit=phi_unit_var.get(); current_value_str=phi_var.get(); current_value=float(current_value_str); target_range=get_phi_range(); new_format_spec=get_phi_format(); new_label_text="Phase (φ radians):" if current_unit=='rad' else "Phase (φ degrees):"; phi_label_var.set(new_label_text); min_val,max_val=target_range; phi_slider.config(from_=min_val,to=max_val); clamped_value=max(min_val,min(current_value,max_val)); phi_slider.set(clamped_value); phi_var.set(new_format_spec.format(clamped_value));
    except ValueError: print(f"Invalid numeric value '{current_value_str}' during unit change."); return
    except Exception as e: print(f"Error updating phase unit: {e}"); traceback.print_exc(); return
    is_plot_initialized = False; update_plot()

def set_phase_value(angle_in_degrees):
    global phi_slider, phi_var, phi_unit_var
    if not all([phi_slider, phi_var, phi_unit_var]): return
    try: current_unit=phi_unit_var.get(); target_range=get_phi_range(); format_spec=get_phi_format(); min_val,max_val=target_range; value_to_set=0.0;
    except Exception as e: print(f"Error getting phase params: {e}"); return
    if current_unit=='deg':value_to_set=float(angle_in_degrees)
    else:value_to_set=np.deg2rad(float(angle_in_degrees))
    clamped_value=max(min_val,min(value_to_set,max_val)); phi_slider.set(clamped_value); phi_var.set(format_spec.format(clamped_value))

# --- Button Redraw Functions (Corrected) ---
def perform_redraw_buttons():
    """Rearranges Quick Set buttons based on available width."""
    global quick_set_buttons, button_wrapper_frame, redraw_timer_id
    redraw_timer_id=None;
    if not button_wrapper_frame or not quick_set_buttons: return
    try:
        if not button_wrapper_frame.winfo_exists(): return
        available_width=button_wrapper_frame.winfo_width();
        if available_width<=1: return
        for btn in quick_set_buttons: btn.grid_forget()
        current_x=0; current_row=0; col_index=0; padding_x=2; pady=2
        for btn in quick_set_buttons:
            try: btn_width = btn.winfo_reqwidth() # Get current width
            except tk.TclError: btn_width = 50
            if current_x>0 and(current_x+btn_width+padding_x*2>available_width): current_row+=1; current_x=0; col_index=0
            btn.grid(row=current_row,column=col_index,sticky='w',padx=padding_x,pady=pady)
            current_x+=btn_width+padding_x*2; col_index+=1
    except tk.TclError as e: print(f"TclError during button redraw: {e}")
    except Exception as e: print(f"Error performing redraw: {e}"); traceback.print_exc()

def schedule_redraw_buttons(event):
    """Schedules the button redraw function to run after a short delay."""
    global redraw_timer_id, root
    if redraw_timer_id is not None:
        try: root.after_cancel(redraw_timer_id)
        except ValueError: pass
        except Exception as e: print(f"Error cancelling redraw timer: {e}")
    redraw_timer_id=root.after(100, lambda: perform_redraw_buttons())


def apply_theme(theme_name):
    """Applies the selected visual theme AND FONT SIZE to the GUI and plots."""
    global root, style, fig, ax, canvas, is_plot_initialized, bg_color, text_color, grid_major_color, grid_minor_color, spine_color, trace_color_input, trace_color_sweep, trace_color_yt_fwd, trace_color_yt_ret, ax_bg_color, tk_bg_color, tk_fg_color, fig_bg_color, button_bg_color, button_active_bg_color
    global font_size_var, global_entry_widgets # Keep Entry workaround list

    print(f"Applying theme: {theme_name}"); theme_settings = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
    tk_bg_color=theme_settings['tk_bg']; tk_fg_color=theme_settings['tk_fg']; fig_bg_color=theme_settings['fig_bg']; ax_bg_color=theme_settings['ax_bg']; text_color=theme_settings['text']; grid_major_color=theme_settings['grid_major']; grid_minor_color=theme_settings['grid_minor']; spine_color=theme_settings['spine']; trace_color_input=theme_settings['trace_input']; trace_color_sweep=theme_settings['trace_sweep']; trace_color_yt_fwd=theme_settings['trace_yt_fwd']; trace_color_yt_ret=theme_settings['trace_yt_ret']; button_bg_color=theme_settings['button_bg']; button_active_bg_color=theme_settings['button_active_bg']

    try:
        base_font_size = DEFAULT_BASE_FONT_SIZE
        if font_size_var:
            try: base_font_size = int(font_size_var.get())
            except (ValueError, tk.TclError): font_size_var.set(str(DEFAULT_BASE_FONT_SIZE)); base_font_size = DEFAULT_BASE_FONT_SIZE

        selected_ttk_theme=theme_settings.get('ttk_theme','default'); available_themes=style.theme_names()
        if selected_ttk_theme in available_themes: style.theme_use(selected_ttk_theme)
        else: style.theme_use('default'); print(f"Warning: ttk theme '{selected_ttk_theme}' not found.")

        default_font_family = "Arial"
        try: default_font = tkFont.nametofont("TkDefaultFont"); default_font_family = default_font.actual("family")
        except tk.TclError: print("Could not get default font family, using Arial.")
        label_size = base_font_size + 1; entry_size = base_font_size; title_size = base_font_size + 3; radio_size = base_font_size; button_size = base_font_size -1; quick_set_label_size = radio_size
        combobox_size = base_font_size

        # Configure styles with new sizes and theme colors
        style.configure('.', background=tk_bg_color, foreground=tk_fg_color, font=(default_font_family, base_font_size))
        style.configure('TFrame', background=tk_bg_color)
        style.configure('TLabel', foreground=tk_fg_color, background=tk_bg_color, font=(default_font_family, label_size))
        style.configure('Title.TLabel', foreground=tk_fg_color, background=tk_bg_color, font=(default_font_family, title_size, 'bold'))
        style.configure('TRadiobutton', foreground=tk_fg_color, background=tk_bg_color, font=(default_font_family, radio_size)); style.map('TRadiobutton',background=[('active',tk_bg_color)]);
        style.configure('TSeparator', background=grid_major_color)
        combobox_font_tuple = (default_font_family, combobox_size)
        # Configure Combobox style (visual effect on displayed text may vary)
        style.configure('TCombobox', foreground=tk_fg_color, fieldbackground=tk_bg_color, selectbackground=tk_bg_color, background=tk_bg_color, font=combobox_font_tuple); style.map('TCombobox',fieldbackground=[('readonly',tk_bg_color)],selectbackground=[('readonly',tk_bg_color)],selectforeground=[('readonly',tk_fg_color)]);
        style.configure('TCombobox.Listbox', font=combobox_font_tuple, background=tk_bg_color, foreground=tk_fg_color)
        style.configure('TScale', background=tk_bg_color)
        entry_font_tuple = (default_font_family, entry_size)
        style.configure('TEntry', foreground=tk_fg_color, fieldbackground=tk_bg_color, insertcolor=tk_fg_color, font=entry_font_tuple); style.map('TEntry', foreground=[('disabled', grid_major_color)]);
        style.configure("QuickSet.TButton", foreground=tk_fg_color, background=button_bg_color, font=(default_font_family, button_size)); style.map("QuickSet.TButton", background=[('active', button_active_bg_color)]);
        style.configure("QuickSetLabel.TLabel", foreground=tk_fg_color, background=tk_bg_color, font=(default_font_family, quick_set_label_size))

        # --- Explicitly update Entry widget fonts (Workaround) ---
        for entry_widget in global_entry_widgets:
             try: entry_widget.configure(font=entry_font_tuple)
             except tk.TclError as e: print(f"Warning: Could not configure font for an entry widget: {e}")

        # --- Explicit Combobox font workaround REMOVED ---

        # --- Update Plot ---
        if fig: fig.patch.set_facecolor(fig_bg_color);
        current_title = "Oscilloscope Simulation"
        if fig and fig.texts: current_title = fig.texts[0].get_text()
        fig.suptitle(current_title, fontsize=title_size+2, color=text_color)
        is_plot_initialized = False; update_plot();
        if button_wrapper_frame: schedule_redraw_buttons(event=None)
    except Exception as e: print(f"Error applying theme '{theme_name}': {e}"); traceback.print_exc()

def on_theme_change(event=None):
    selected_theme = theme_var.get();
    if selected_theme: apply_theme(selected_theme)

def on_font_size_change(*args):
    global theme_var
    current_theme = theme_var.get() if theme_var else DEFAULT_THEME
    apply_theme(current_theme)

# --- GUI Setup ---
root = tk.Tk(); root.title("Oscilloscope Simulation"); style = ttk.Style()

style.configure("TRadiobutton"); style.configure("QuickSet.TButton", padding=(4,2))

main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashwidth=8, relief=tk.RAISED, bg='grey'); main_pane.pack(fill=tk.BOTH, expand=True)
control_frame = ttk.Frame(root, padding="15 10", style='TFrame'); plot_frame = ttk.Frame(root, style='TFrame')
main_pane.add(control_frame, minsize=400, sticky="nsew"); main_pane.add(plot_frame, minsize=450, sticky="nsew")

# --- Control Creation Helper ---
def create_control(parent, label_text_provider, var, slider_range_provider, default_val, format_spec_provider):
    """Creates a standard control group (Label, Slider, Entry) and packs it."""
    global global_entry_widgets
    frame=ttk.Frame(parent);frame.pack(fill=tk.X,pady=6);label_text=label_text_provider();
    # Rely on style for Label font
    if isinstance(label_text,tk.Variable):label=ttk.Label(frame,textvariable=label_text, anchor='w')
    else:label=ttk.Label(frame,text=label_text, anchor='w')
    label.pack(side=tk.TOP,fill=tk.X,padx=5,pady=(0,3));widget_frame=ttk.Frame(frame);widget_frame.pack(fill=tk.X)
    min_val,max_val=slider_range_provider();slider=ttk.Scale(widget_frame,from_=min_val,to=max_val,orient=tk.HORIZONTAL,length=280);slider.set(default_val);slider.pack(side=tk.LEFT,fill=tk.X,expand=True,padx=(5,5))
    entry=ttk.Entry(widget_frame,textvariable=var,width=8, style='TEntry');entry.pack(side=tk.RIGHT,padx=(0,5)) # Font set by style & workaround
    global_entry_widgets.append(entry) # Add for workaround
    slider.config(command=lambda val: update_plot())
    handler=create_entry_handler(var,slider,slider_range_provider,format_spec_provider);
    entry.bind('<Return>',handler)
    return slider

# --- Populate control_frame ---
title_label = ttk.Label(control_frame, text="Oscilloscope Controls", style='Title.TLabel'); title_label.pack(pady=(0, 5), anchor='w')
config_frame = ttk.Frame(control_frame); config_frame.pack(fill=tk.X, pady=(5,10))
theme_frame = ttk.Frame(config_frame); theme_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10));
ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT, padx=(0, 5)); # Font from style
theme_var = tk.StringVar(value=DEFAULT_THEME);
theme_combo = ttk.Combobox(theme_frame, textvariable=theme_var, values=list(THEMES.keys()), state="readonly", width=12); # Font from style
theme_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5); theme_combo.bind('<<ComboboxSelected>>', on_theme_change)
font_size_frame = ttk.Frame(config_frame); font_size_frame.pack(side=tk.LEFT, padx=(10,0))
ttk.Label(font_size_frame, text="Font Size:").pack(side=tk.LEFT, padx=(0,5)); # Font from style
font_size_var = tk.StringVar(value=str(DEFAULT_BASE_FONT_SIZE))
font_size_values = [str(size) for size in FONT_SIZES]
font_size_combo = ttk.Combobox(font_size_frame, textvariable=font_size_var, values=font_size_values, state="readonly", width=4) # Font from style
font_size_combo.pack(side=tk.LEFT)
font_size_combo.bind('<<ComboboxSelected>>', on_font_size_change)
ttk.Separator(control_frame,orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

# --- Input Signal Section ---
input_title_var = tk.StringVar(value=f"Input Signal: A {DEFAULT_INPUT_FUNC}(ωt + φ)")
ttk.Label(control_frame, textvariable=input_title_var, style='Title.TLabel').pack(pady=(0, 5), anchor='w')
input_func_frame = ttk.Frame(control_frame); input_func_frame.pack(fill=tk.X, padx=5, pady=(0,5))
input_func_var = tk.StringVar(value=DEFAULT_INPUT_FUNC)
sin_radio = ttk.Radiobutton(input_func_frame, text="sin", variable=input_func_var, value='sin', command=update_input_title, style='TRadiobutton'); cos_radio = ttk.Radiobutton(input_func_frame, text="cos", variable=input_func_var, value='cos', command=update_input_title, style='TRadiobutton'); sin_radio.pack(side=tk.LEFT, padx=5); cos_radio.pack(side=tk.LEFT, padx=5) # Font from style
amp_var=tk.StringVar(value=f"{DEFAULT_AMP:.2f}"); amp_slider=create_control(control_frame,lambda:"Amplitude (A):",amp_var,get_amp_range,DEFAULT_AMP,lambda:"{:.2f}")
omega_var=tk.StringVar(value=f"{DEFAULT_X_FACTOR:.2f}"); omega_slider=create_control(control_frame, lambda: "Ang. Freq Factor (x) [ω = x*π]:", omega_var, get_xfactor_range, DEFAULT_X_FACTOR, lambda: "{:.2f}")
phi_unit_var=tk.StringVar(value=DEFAULT_PHI_UNIT); phi_var=tk.StringVar(value=f"{DEFAULT_PHI:.1f}"); phi_label_var=tk.StringVar(value="Phase (φ degrees):")
phi_slider=create_control(control_frame,lambda:phi_label_var,phi_var,get_phi_range,DEFAULT_PHI,get_phi_format)
unit_frame=ttk.Frame(control_frame); unit_frame.pack(fill=tk.X,padx=5,pady=(3,3));
deg_radio = ttk.Radiobutton(unit_frame,text="Degrees",variable=phi_unit_var,value='deg',command=update_phase_unit,style='TRadiobutton'); rad_radio = ttk.Radiobutton(unit_frame,text="Radians",variable=phi_unit_var,value='rad',command=update_phase_unit,style='TRadiobutton'); # Font from style
deg_radio.pack(side=tk.LEFT,padx=5); rad_radio.pack(side=tk.LEFT,padx=5)
quick_phase_frame=ttk.Frame(control_frame); quick_phase_frame.pack(fill=tk.X,padx=5,pady=(3,10));
ttk.Label(quick_phase_frame,text="Quick Set φ:", style="QuickSetLabel.TLabel").pack(side=tk.LEFT,padx=(0,5),anchor='w'); # Font from style
button_wrapper_frame = ttk.Frame(quick_phase_frame); button_wrapper_frame.pack(side=tk.LEFT, fill=tk.X, expand=True);
button_wrapper_frame.bind('<Configure>', schedule_redraw_buttons)
quick_angles_deg = [-90, -60, -45, -30, 0, 30, 45, 60, 90]; angle_labels = {-90:"-90°/-π/2",-60:"-60°/-π/3",-45:"-45°/-π/4",-30:"-30°/-π/6",0:"0°",30:"30°/π/6",45:"45°/π/4",60:"60°/π/3",90:"90°/π/2"}
quick_set_buttons = [];
for i, angle_deg in enumerate(quick_angles_deg):
    btn_text = angle_labels.get(angle_deg, f"{angle_deg}°")
    button = ttk.Button(button_wrapper_frame, text=btn_text, style="QuickSet.TButton", command=lambda deg=angle_deg: set_phase_value(deg)) # Font from style
    button.grid(row=0, column=i, sticky='w', padx=2, pady=1)
    quick_set_buttons.append(button)
ttk.Separator(control_frame,orient=tk.HORIZONTAL).pack(fill=tk.X,pady=15)

# --- Sweep Parameters Section ---
ttk.Label(control_frame,text="Sweep Parameters", style='Title.TLabel').pack(pady=(0,15),anchor='w')
tqt_factor_var=tk.StringVar(value=f"{DEFAULT_TQT_FACTOR:.2f}"); tqt_factor_slider=create_control(control_frame,lambda:"Fwd Sweep Factor (x Ty):",tqt_factor_var,get_t_factor_range,DEFAULT_TQT_FACTOR,lambda:"{:.2f}")
tqn_factor_var=tk.StringVar(value=f"{DEFAULT_TQN_FACTOR:.2f}"); tqn_factor_slider=create_control(control_frame,lambda:"Ret Sweep Factor (x Ty):",tqn_factor_var,get_t_factor_range,DEFAULT_TQN_FACTOR,lambda:"{:.2f}")

# --- Populate plot_frame ---
fig, ax = plt.subplots(3, 1, figsize=(10, 9)); fig.suptitle('Oscilloscope Simulation', fontsize=16) # Adjusted figsize
canvas = FigureCanvasTkAgg(fig, master=plot_frame); canvas_widget = canvas.get_tk_widget(); canvas_widget.pack(fill=tk.BOTH, expand=True)

# --- Initial Setup ---
def final_initialization():
    global is_plot_initialized, quick_set_buttons
    root.update_idletasks()
    # Button width caching removed
    apply_theme(DEFAULT_THEME)
    root.after(50, perform_redraw_buttons) # Initial draw after widths are known


# --- Main Loop ---
root.after(50, final_initialization)
root.mainloop()





