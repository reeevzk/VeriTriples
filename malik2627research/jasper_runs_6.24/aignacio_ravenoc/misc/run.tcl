clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src -incdir /home/rk6650/VeriTriples/malik2627research/src/include -incdir /home/rk6650/VeriTriples/malik2627research/src/ni -incdir /home/rk6650/VeriTriples/malik2627research/src/router /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include/ravenoc_pkg.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src -incdir /home/rk6650/VeriTriples/malik2627research/src/include -incdir /home/rk6650/VeriTriples/malik2627research/src/ni -incdir /home/rk6650/VeriTriples/malik2627research/src/router /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include/ravenoc_axi_fnc.svh }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src -incdir /home/rk6650/VeriTriples/malik2627research/src/include -incdir /home/rk6650/VeriTriples/malik2627research/src/ni -incdir /home/rk6650/VeriTriples/malik2627research/src/router /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include/ravenoc_structs.svh }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src -incdir /home/rk6650/VeriTriples/malik2627research/src/include -incdir /home/rk6650/VeriTriples/malik2627research/src/ni -incdir /home/rk6650/VeriTriples/malik2627research/src/router /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/router/fifo.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src -incdir /home/rk6650/VeriTriples/malik2627research/src/include -incdir /home/rk6650/VeriTriples/malik2627research/src/ni -incdir /home/rk6650/VeriTriples/malik2627research/src/router /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/ni/async_gp_fifo.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src -incdir /home/rk6650/VeriTriples/malik2627research/src/include -incdir /home/rk6650/VeriTriples/malik2627research/src/ni -incdir /home/rk6650/VeriTriples/malik2627research/src/router /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include/ravenoc_defines.svh }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src -incdir /home/rk6650/VeriTriples/malik2627research/src/include -incdir /home/rk6650/VeriTriples/malik2627research/src/ni -incdir /home/rk6650/VeriTriples/malik2627research/src/router /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/router/rr_arbiter.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src -incdir /home/rk6650/VeriTriples/malik2627research/src/include -incdir /home/rk6650/VeriTriples/malik2627research/src/ni -incdir /home/rk6650/VeriTriples/malik2627research/src/router /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/ravenoc_wrapper.sv }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/include -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/src -incdir /home/rk6650/VeriTriples/malik2627research/src/include -incdir /home/rk6650/VeriTriples/malik2627research/src/ni -incdir /home/rk6650/VeriTriples/malik2627research/src/router /home/rk6650/VeriTriples/malik2627research/repos_6.24/aignacio_ravenoc/src/router/vc_buffer.sv }


            if {[catch {elaborate -top async_gp_fifo} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/aignacio_ravenoc/misc/results.rpt
report_vacuity -out jasper_runs_6.24/aignacio_ravenoc/misc/vacuity.rpt
exit
