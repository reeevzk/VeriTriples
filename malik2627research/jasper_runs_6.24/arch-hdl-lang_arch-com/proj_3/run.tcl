clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples /home/rk6650/VeriTriples/malik2627research/repos_6.24/arch-hdl-lang_arch-com/examples/lz4_block_decoder.sv }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/examples /home/rk6650/VeriTriples/malik2627research/repos_6.24/arch-hdl-lang_arch-com/examples/lz4_block_decoder.sv }


            if {[catch {elaborate -top Lz4BlockDecoder} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/arch-hdl-lang_arch-com/proj_3/results.rpt
report_vacuity -out jasper_runs_6.24/arch-hdl-lang_arch-com/proj_3/vacuity.rpt
exit
