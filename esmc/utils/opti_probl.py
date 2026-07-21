import numpy as np
import os
import logging
import pandas as pd
import csv
from pathlib import Path
import pickle
from amplpy import AMPL, Environment, DataFrame
from esmc.postprocessing import amplpy2pd as a2p

# todo add possibility to choose solver with options aswell
class OptiProbl:
    """

    The OptiProbl class allows to set an optimization problem in ampl, solve it,
     and interface with it trough the amplpy API and some additionnal functions

    Parameters
    ----------
    mod_path : pathlib.Path
        Specifies the path of the .mod file defining the LP problem in ampl syntax
    data_path : list(pathlib.Path)
        List specifying the path of the different .dat files with the data of the LP problem
        in ampl syntax
    options : dict
        Dictionary of the different options for ampl and the cplex solver

    """

    def __init__(self, mod_path=list(), data_path=list(), options=dict(), solver='cplex', ampl_path=None, set_ampl=True):
        """

        Parameters
        ----------
        mod_path
        data_path
        options
        solver
        ampl_path
        set_ampl
        """
        # instantiate different attributes
        if len(mod_path) == 0:
            self.dir = Path()
        else:
            self.dir = mod_path[0].parent

        self.mod_path = mod_path
        self.data_path = data_path
        self.options = options
        if set_ampl:
            self.ampl = self.set_ampl(mod_path, data_path, solver, ampl_path)
        else:
            self.ampl = None
        self.vars = list()
        self.params = list()
        self.sets = dict()
        self.inputs = dict()
        self.t = None
        self.outputs = dict()

        return

    def run_ampl(self, iis_diagnostic=False):
        """
        Ejecuta la optimización con AMPL. Si iis_diagnostic=True, activa el
        'iisfind' de CPLEX ANTES del solve para que, si el modelo resulta
        infeasible, se pueda leer el IIS exacto (conjunto irreducible de
        restricciones/variables en conflicto) via los sufijos .iis de AMPL.

        iis_diagnostic queda en False por defecto: los runs normales (factibles)
        no deben ver modificado ni su solve ni sus opciones de cplex.
        """
        self.iis_cons = None
        self.iis_vars = None
        try:
            # Configurar opciones del solver
            for o in self.options:
                self.ampl.setOption(o, self.options[o])

            if iis_diagnostic:
                # iisfind DEBE fijarse ANTES de solve(): CPLEX solo calcula el IIS
                # como parte del mismo solve que detecta la infeasibilidad; fijarlo
                # después (como en el intento anterior) llega demasiado tarde.
                base_cplex_options = self.options.get('cplex_options', '')
                self.ampl.setOption('cplex_options', (base_cplex_options + ' iisfind=1').strip())

            # Resolver el modelo
            self.ampl.solve()

            # Verificar el estado del solver
            solve_result = self.ampl.getValue('solve_result_num')
            if solve_result not in [0, 1]:  # 0 = Óptimo, 1 = Factible
                print("El modelo es primal-dual infeasible o no tiene solución factible.")

                if iis_diagnostic:
                    # AMPL no tiene un comando "write iis;". CPLEX expone el IIS via
                    # el sufijo .iis en variables/restricciones, con valores:
                    # "non" = no forma parte del IIS, "low"/"upp" = la cota
                    # inferior/superior forma parte del IIS, "fix" = la restricción
                    # de igualdad forma parte del IIS.
                    try:
                        cons_df = self.ampl.getData('_conname, _con.iis').toPandas()
                        vars_df = self.ampl.getData('_varname, _var.iis').toPandas()
                        self.iis_cons = cons_df[cons_df['_con.iis'] != 'non']
                        self.iis_vars = vars_df[vars_df['_var.iis'] != 'non']
                        print("=== IIS_REPORT_START ===")
                        print(self.iis_cons.to_string())
                        print(self.iis_vars.to_string())
                        print("=== IIS_REPORT_END ===")
                    except Exception as e:
                        print(f"Error al generar el reporte IIS: {e}")

            else:
                print("El modelo ha sido resuelto satisfactoriamente.")

            # Reinitialize log options to disable further logging
            self.ampl.setOption('show_stats', 0)
            self.ampl.setOption('times', 0)
            self.ampl.setOption('gentimes', 0)

        except Exception as e:
            print(f"Ocurrió un error durante la optimización: {e}")
            raise RuntimeError("La optimización con AMPL falló. Consulta los detalles arriba.")

    def run_feasopt(self, con_names=None):
        """
        Diagnóstico complementario al IIS: relajación mínima de factibilidad
        (CPLEX 'feasopt=2' -> "find a 'best' solution among the relaxed
        feasible points", cplex_options README). NO debe llamarse desde
        run_ampl ni desde un run normal: es un método explícito, a invocar
        a mano cuando el IIS es demasiado grande/ambiguo para interpretarse
        directamente.

        FeasOpt no modifica el modelo: la solución que devuelve sigue siendo
        infeasible respecto a los bounds/rhs originales. Por lo tanto acá no
        leemos ningún suffix propietario de relajación; en su lugar se
        recalcula, para cada restricción indicada (típicamente las del IIS),
        el delta = valor del cuerpo de la restricción tras el resolve - el
        bound original que violaría, lo cual es la relajación mínima real
        necesaria para volver factible.

        Parameters
        ----------
        con_names : list(str) or None
            Nombres (con subíndices) de las restricciones a diagnosticar,
            normalmente self.iis_cons['_conname'].tolist() de un run_ampl
            previo con iis_diagnostic=True. Si None, se usa self.iis_cons.

        Returns
        -------
        pandas.DataFrame con columnas [name, body, lb, ub, delta_lb, delta_ub]
        """
        if con_names is None:
            if self.iis_cons is None or len(self.iis_cons) == 0:
                raise ValueError("No iis_cons available: run run_ampl(iis_diagnostic=True) first "
                                  "or pass con_names explicitly.")
            con_names = set(self.iis_cons['_conname'].tolist())

        base_cplex_options = self.options.get('cplex_options', '')
        self.ampl.setOption('cplex_options', (base_cplex_options + ' feasopt=2').strip())
        self.ampl.solve()

        # Same generic _con[i] indexing as the IIS report (avoids re-parsing the
        # bracketed instance name back into an index tuple for ampl.getConstraint).
        df = self.ampl.getData('_conname, _con.body, _con.lb, _con.ub').toPandas()
        df = df[df['_conname'].isin(con_names)].copy()
        df['delta_lb'] = (df['_con.lb'] - df['_con.body']).clip(lower=0.0)
        df['delta_ub'] = (df['_con.body'] - df['_con.ub']).clip(lower=0.0)
        return df.rename(columns={'_conname': 'name', '_con.body': 'body',
                                   '_con.lb': 'lb', '_con.ub': 'ub'})

    def get_solve_info(self):
        """

       Get the solving info (time and result) and stores it into t attribute

        """
        logging.info('Getting solve_info')
        self.t = list()
        self.t.append(self.ampl.getData('_ampl_elapsed_time;').toList()[0])
        self.t.append(self.ampl.getData('_solve_elapsed_time;').toList()[0])
        self.t.append(self.ampl.getData('solve_result_num;').toList()[0])
        print('[_ampl_elapsed_time, _solve_elapsed_time, solve_result_num]')
        print(self.t)
        # TODO understand why doesn't work with kmedoid_clustering
        return

    def get_inputs(self):
        """

        Get the name of variables and parameters and the sets

        """
        # get values of attributes
        self.get_vars()
        self.get_params()
        self.get_sets()

    def get_vars(self):
        """

        Get the name of the LP optimization problem's variables

        """
        self.vars = list()
        for name, values in self.ampl.getVariables():
            self.vars.append(name)

    def get_params(self):
        """

        Get the name of the LP optimization problem's parameters

               """
        self.params = list()
        for n, p in self.ampl.getParameters():
            self.params.append(n)

    def get_sets(self):
        #TODO update to a more robust version
        """

               Function to sets of the LP optimization problem

        """
        self.sets = dict()
        for name, obj in self.ampl.getSets():
            if len(obj.instances()) <= 1:
                try:
                    self.sets[name] = obj.getValues().toList()
                except Exception as e:
                    logging.warning(str(name) + ' set not working, replacing it by a empty list')
                    self.sets [name] = list()
            else:
                self.sets[name] = self.get_subset(obj)

    def print_inputs(self, directory=None):
        """

        Prints the sets, parameters' names and variables' names of the LP optimization problem

        Parameters
        ----------
        directory : pathlib.Path
        Path of the directory where to save the inputs

        """
        # default directory
        if directory is None:
            directory = self.dir / 'inputs'
        # creating inputs dir
        directory.mkdir(parents=True, exist_ok=True)

        # if params is empty get all inputs
        if not self.params:
            self.get_inputs()
        # printing inputs
        a2p.print_json(self.sets, directory / 'sets.json')
        a2p.print_json(self.params, directory / 'parameters.json')
        a2p.print_json(self.vars, directory / 'variables.json')

        return

    # def get_outputs(self):
    #     """
    #
    #            Function to extract the values of each variable after running the optimization problem
    #
    #                   """
    #     # function to get the outputs of ampl under the form of a dict filled with one df for each variable
    #     amplpy_sol = self.ampl.getVariables()
    #     self.outputs = dict()
    #     for name, var in amplpy_sol:
    #         self.outputs[name] = self.to_pd(var.getValues())

    def get_param(self, param_name: str):
        """Function to extract the mentioned parameter and store it into self.inputs

        Parameters
        ----------
        param_name: str
        Name of the parameter to extract from the optimisation problem results. Should be written as in the .mod file

        Returns
        -------
        param: pd.DataFrame()
        DataFrame containing the values of the different elements of the parameter.
        The n first columns give the n sets on which it is indexed
        and the last column give the value obtained from the optimization.

        """
        ampl_param = self.ampl.getParameter(param_name)
        # Getting the names of the sets
        indexing_sets = [s.capitalize() for s in ampl_param.getIndexingSets()]
        # Getting the data of the variable into a pandas dataframe
        amplpy_df = ampl_param.getValues()
        param = amplpy_df.toPandas()
        # getting the number of indices. If var has more then 1 index, we set it as a MultiIndex
        n_indices = amplpy_df.getNumIndices()
        if n_indices > 1:
            param.index = pd.MultiIndex.from_tuples(param.index, names=indexing_sets)
        else:
            param.index = pd.Index(param.index, name=indexing_sets[0])
        # self.to_pd(ampl_var.getValues()).rename(columns={(var_name+'.val'):var_name})
        self.inputs[param_name] = param
        return param


    def get_var(self, var_name:str):
        """Function to extract the mentioned variable and store it into self.outputs

        Parameters
        ----------
        var_name: str
        Name of the variable to extract from the optimisation problem results. Should be written as in the .mod file

        Returns
        -------
        var: pd.DataFrame()
        DataFrame containing the values of the different elements of the variable.
        The n first columns give the n sets on which it is indexed
        and the last column give the value obtained from the optimization.

        """
        ampl_var = self.ampl.getVariable(var_name)
        # Getting the names of the sets
        indexing_sets = [s.capitalize() for s in ampl_var.getIndexingSets()]
        # Getting the data of the variable into a pandas dataframe
        df = ampl_var.get_values().to_pandas()
        df.index.names = indexing_sets
        # getting rid of '.val' (4 trailing characters of the string) into columns names such that the name of the columns correspond to the variable
        df.rename(columns=lambda x: x[:-4], inplace=True)
        #self.to_pd(ampl_var.getValues()).rename(columns={(var_name+'.val'):var_name})
        self.outputs[var_name] = df
        return df

    # TODO check if not used

    # def print_outputs(self, directory=None, solve_time=False):
    #     """
    #
    #     Prints the outputs (dictionary of pd.DataFrame()) into a pickle file
    #
    #     Parameters
    #     ----------
    #     directory : pathlib.Path
    #     Path of the directory where to save the dataframes
    #
    #     """
    #     # default directory
    #     if directory is None:
    #         directory = self.dir / 'outputs'
    #     # creating outputs dir
    #     directory.mkdir(parents=True, exist_ok=True)
    #     # printing outputs
    #     with open(directory/'outputs.p', 'wb') as handle:
    #         pickle.dump(self.outputs, handle, protocol=pickle.HIGHEST_PROTOCOL)
    #
    #     # for ix, (key, val) in enumerate(self.outputs.items()):
    #     #     val.to_csv(directory / (str(key) + '.csv'))
    #
    #     if solve_time:
    #         if self.t is None:
    #             self.get_solve_info()
    #         with open(directory / 'Solve_time.csv', mode='w', newline='\n') as file:
    #             writer = csv.writer(file, delimiter=AMPL_SEPERATOR, quotechar=' ', quoting=csv.QUOTE_MINIMAL,
    #                                    lineterminator="\n")
    #             writer.writerow(['ampl_elapsed_time', self.t[0]])
    #             writer.writerow(['solve_elapsed_time', self.t[1]])
    #     return

    def read_outputs(self, directory=None):
        """

        Reads the outputs previously printed into csv files to recover a case study without running it again

        Parameters
        ----------
        directory : pathlib.Path
        Path of the directory where the outputs are saved

        """
        # default directory
        if directory is None:
            directory = self.dir / 'outputs'

        with open(directory/'outputs.p', 'rb') as handle:
            self.outputs = pickle.load(handle)

        # # To save as csv

        # #if vars is an empty list, get vars
        # if not self.vars:
        #     self.get_vars()
        # # read outputs
        # self.outputs = dict()
        # for v in self.vars:
        #     self.outputs[v] = pd.read_csv(directory / (v + '.csv'), index_col=0)


    # def remove_outputs(self, directory):
    #     for v in self.vars:
    #         filename = directory / (v + '.csv')
    #         try:
    #             os.remove(filename)
    #         except OSError:
    #             print('Could not erase previous log file ' + filename)

    #############################
    #       STATIC METHODS      #
    #############################

    @staticmethod
    def set_ampl(mod_path=list(), data_path=list(), solver='cplex', ampl_path=None):
        """

        Initialize the AMPL() object containing the LP problem

        Parameters
        ----------
         mod_path : list(pathlib.Path)
        Specifies the path of the .mod files defining the LP problem in ampl syntax

        data_path : list(pathlib.Path)
        List specifying the path of the different .dat files with the data of the LP problem
        in ampl syntax

        solver : str
        Name of the solver (default='cplex')

        ampl_path : None or pathlib.Path
        Default None means ampl is a path variable
        otherwise, give the path to ampl binaries files and solver files

        options : dict
        Dictionary of the different options for ampl and the cplex solver

        Returns
        -------
        ampl object created

        """
        try:
            if ampl_path is None:
                # Create an AMPL instance
                ampl = AMPL()
                # define solver
                ampl.setOption('solver', solver)
            else:
                # Create an AMPL instance
                ampl = AMPL(Environment(binary_directory=str(ampl_path)))#, binary_name='ampl.exe'))
                # define solver
                ampl.setOption('solver', str(Path(ampl_path) / solver))

            # Read the model and data files.
            for m in mod_path:
                ampl.read(m)
            for d in data_path:
                ampl.readData(d)
        except Exception as e:
            print(e)
            raise

        return ampl

    @staticmethod
    def get_subset(my_set):
        """

        Function to extract the subsets of set containing sets from the AMPL() object

               Parameters
               ----------
            my_set : amplpy.set.Set
            2-dimensional set to extract


               Returns
               -------
               d : dict()
               dictionary containing the subsets as lists

               """
        d = dict()
        for n, o in my_set.instances():
            try:
                d[n] = o.getValues().toList()
            except Exception as e:
                logging.warning(str(n) + ' subset not working, , replacing it by a empty list')
                d[n] = list()
        return d

    # @staticmethod
    # def to_pd(amplpy_df):
    #     # TODO check if name of indexes can be nasme of corresponding sets
    #     """
    #
    #            Function to transform an amplpy.DataFrame into pandas.DataFrame for easier manipulation
    #
    #                   Parameters
    #                   ----------
    #                amplpy_df : amplpy.DataFrame
    #                amplpy dataframe to transform
    #
    #
    #                   Returns
    #                   -------
    #                   df : pandas.DataFrame
    #                   DataFrame transformed as 'long' dataframe (can be easily pivoted later)
    #                   """
    #     headers = amplpy_df.getHeaders()
    #     columns = {header: list(amplpy_df.getColumn(header)) for header in headers}
    #     df = pd.DataFrame(columns)
    #     return df